import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from aegisScout.core.models import Lead, Campaign, ActivityLog
from aegisScout.core.database import init_db, engine
from typer.testing import CliRunner
from aegisScout.main import app

def test_campaign_models_and_relationships():
    # Setup temporary database
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        # 1. Create a campaign
        campaign = Campaign(name="Kuafor Campaign", sector_filter="kuaför", location_filter="Kadıköy")
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        assert campaign.id is not None
        assert campaign.name == "Kuafor Campaign"

        # 2. Create and associate leads
        lead1 = Lead(business_name="Kuafor Ahmet", sector="kuaför", address="Kadıköy, İstanbul", campaign_id=campaign.id)
        lead2 = Lead(business_name="Kuafor Mehmet", sector="kuaför", address="Kadıköy, İstanbul", campaign_id=campaign.id)
        session.add(lead1)
        session.add(lead2)
        session.commit()

        # 3. Verify relationships
        session.refresh(campaign)
        assert len(campaign.leads) == 2
        assert campaign.leads[0].business_name in ["Kuafor Ahmet", "Kuafor Mehmet"]
        assert campaign.leads[0].campaign == campaign

def test_cli_campaign_commands():
    # Pre-test cleanup to guarantee isolation
    init_db(engine)
    with Session(engine) as session:
        # Delete existing campaign if present from interrupted runs
        old_c = session.exec(select(Campaign).where(Campaign.name == "TestCamp")).first()
        if old_c:
            # Delete associated leads
            leads = session.exec(select(Lead).where(Lead.campaign_id == old_c.id)).all()
            for l in leads:
                session.delete(l)
            session.delete(old_c)
        # Delete the test lead if it exists
        old_l = session.exec(select(Lead).where(Lead.business_name == "Test Berber Ali")).first()
        if old_l:
            session.delete(old_l)
        session.commit()

    runner = CliRunner()

    # 1. Create a campaign via CLI
    result = runner.invoke(app, ["campaign", "create", "--name", "TestCamp", "--sector", "berber"])
    assert result.exit_code == 0
    assert "başarıyla oluşturuldu" in result.output

    # 2. List campaigns via CLI
    result = runner.invoke(app, ["campaign", "list"])
    assert result.exit_code == 0
    assert "TestCamp" in result.output

    # 3. Create a lead and assign it to the campaign
    with Session(engine) as session:
        # Get campaign ID
        c = session.exec(select(Campaign).where(Campaign.name == "TestCamp")).first()
        assert c is not None
        c_id = c.id

        # Insert a lead to assign
        lead = Lead(business_name="Test Berber Ali", sector="berber", address="Beşiktaş, İstanbul")
        session.add(lead)
        session.commit()
        lead_id = lead.id

    # Assign lead to campaign
    result = runner.invoke(app, ["campaign", "assign", "--campaign-id", str(c_id), "--lead-id", str(lead_id)])
    assert result.exit_code == 0
    assert "başarıyla" in result.output and "kampanyasına atandı" in result.output

    # Show campaign via CLI
    result = runner.invoke(app, ["campaign", "show", str(c_id)])
    assert result.exit_code == 0
    assert "Test Berber Ali" in result.output

    # 4. Clean up
    with Session(engine) as session:
        lead_db = session.get(Lead, lead_id)
        if lead_db:
            session.delete(lead_db)
        camp_db = session.get(Campaign, c_id)
        if camp_db:
            session.delete(camp_db)
        session.commit()


def test_gui_campaign_commands():
    from aegisScout.gui import GuiApi
    api = GuiApi()

    # Pre-test cleanup
    init_db(engine)
    with Session(engine) as session:
        old_c = session.exec(select(Campaign).where(Campaign.name == "Test GUI Campaign")).first()
        if old_c:
            leads = session.exec(select(Lead).where(Lead.campaign_id == old_c.id)).all()
            for l in leads:
                session.delete(l)
            session.delete(old_c)
        old_l = session.exec(select(Lead).where(Lead.business_name == "Test GUI Lead")).first()
        if old_l:
            session.delete(old_l)
        session.commit()

    # 1. Create campaign via GuiApi
    res = api.create_campaign("Test GUI Campaign", sector_filter="kuaför", location_filter="Kadıköy")
    assert "success" in res and res["success"] is True
    campaign_id = res["id"]

    # 2. Verify it is listed in get_campaigns()
    campaigns = api.get_campaigns()
    assert isinstance(campaigns, list)
    found = [c for c in campaigns if c["name"] == "Test GUI Campaign"]
    assert len(found) == 1
    assert found[0]["total_leads"] == 0

    # 3. Create a lead and assign it via GuiApi
    with Session(engine) as session:
        lead = Lead(business_name="Test GUI Lead", sector="kuaför", address="Kadıköy Merkez")
        session.add(lead)
        session.commit()
        lead_id = lead.id

    assign_res = api.assign_lead_to_campaign(campaign_id, lead_id=lead_id)
    assert assign_res.get("success") is True
    assert assign_res.get("assigned") == 1

    # 4. Verify campaign details and associated leads
    details = api.get_campaign_details(campaign_id)
    assert "campaign" in details
    assert details["campaign"]["name"] == "Test GUI Campaign"
    assert len(details["leads"]) == 1
    assert details["leads"][0]["business_name"] == "Test GUI Lead"

    # 5. Clean up
    with Session(engine) as session:
        l_db = session.get(Lead, lead_id)
        if l_db:
            session.delete(l_db)
        c_db = session.get(Campaign, campaign_id)
        if c_db:
            session.delete(c_db)
        session.commit()

