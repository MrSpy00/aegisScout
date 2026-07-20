import asyncio
import threading
from typing import Dict, Any, Callable, List, Optional
from aegisScout.utils.logger import get_logger

logger = get_logger("core.task_queue")


class QueuedTask:
    def __init__(self, task_id: str, name: str, coro_func: Callable, *args, **kwargs):
        self.id = task_id
        self.name = name
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
        self.status = "pending"  # pending, running, paused, completed, cancelled, failed
        self.progress = 0.0
        self.error: Optional[str] = None
        self.resume_event: Optional[asyncio.Event] = None
        self.asyncio_task: Optional[asyncio.Task] = None


class TaskQueueManager:
    _instance: Optional['TaskQueueManager'] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'TaskQueueManager':
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.tasks: Dict[str, QueuedTask] = {}
        
        # Start background event loop in a daemon thread
        self._loop = asyncio.new_event_loop()
        self._queue = None
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._queue = asyncio.Queue()
        self._loop.run_until_complete(self._worker_loop())

    async def _worker_loop(self):
        logger.info("TaskQueueManager worker loop started on background thread.")
        while True:
            try:
                task: QueuedTask = await self._queue.get()
                if task.status == "cancelled":
                    self._queue.task_done()
                    continue
                
                task.status = "running"
                task.resume_event = asyncio.Event()
                task.resume_event.set()
                logger.info(f"Starting task on thread loop: {task.id} ({task.name})")
                
                task.kwargs["task_id"] = task.id
                
                # Wrap the coroutine execution
                async def run_and_track():
                    try:
                        await task.coro_func(*task.args, **task.kwargs)
                        if task.status == "running" or task.status == "paused":
                            task.status = "completed"
                            task.progress = 100.0
                            logger.info(f"Task completed successfully: {task.id}")
                    except asyncio.CancelledError:
                        task.status = "cancelled"
                        logger.info(f"Task was cancelled: {task.id}")
                    except Exception as e:
                        task.status = "failed"
                        task.error = str(e)
                        logger.error(f"Task failed: {task.id} - {e}")

                task.asyncio_task = self._loop.create_task(run_and_track())
                await task.asyncio_task
                
                self._queue.task_done()
            except Exception as e:
                logger.error(f"Error in task queue worker loop: {e}")
                await asyncio.sleep(1)

    def add_task(self, task_id: str, name: str, coro_func: Callable, *args, **kwargs) -> str:
        if task_id in self.tasks:
            raise ValueError(f"Task with ID {task_id} already exists.")
            
        task = QueuedTask(task_id, name, coro_func, *args, **kwargs)
        self.tasks[task_id] = task
        
        self._loop.call_soon_threadsafe(self._queue.put_nowait, task)
        logger.info(f"Queued task thread-safely: {task_id}")
        return task_id

    async def wait_if_paused(self, task_id: str):
        task = self.tasks.get(task_id)
        if task and task.resume_event:
            if task.status == "paused":
                logger.info(f"Task {task_id} is paused. Awaiting resume...")
            await task.resume_event.wait()

    def update_progress(self, task_id: str, progress: float):
        task = self.tasks.get(task_id)
        if task:
            task.progress = min(max(progress, 0.0), 100.0)

    def pause_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task.status == "running":
            task.status = "paused"
            if task.resume_event:
                self._loop.call_soon_threadsafe(task.resume_event.clear)
            logger.info(f"Paused task: {task_id}")
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task.status == "paused":
            task.status = "running"
            if task.resume_event:
                self._loop.call_soon_threadsafe(task.resume_event.set)
            logger.info(f"Resumed task: {task_id}")
            return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
            
        if task.status in ("pending", "running", "paused"):
            task.status = "cancelled"
            if task.resume_event:
                self._loop.call_soon_threadsafe(task.resume_event.set)
            if task.asyncio_task:
                self._loop.call_soon_threadsafe(task.asyncio_task.cancel)
            logger.info(f"Cancelled task: {task_id}")
            return True
        return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "progress": task.progress,
            "error": task.error
        }

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        return [self.get_task_status(tid) for tid in self.tasks if self.get_task_status(tid) is not None]
