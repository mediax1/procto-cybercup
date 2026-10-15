import os, subprocess, sys

def run_import(host):
    env=os.environ.copy();env.update({"LAB_VULNERABILITIES_ENABLED":"true","HOST":host,"DATABASE_URL":"sqlite:///./lab-test.db"})
    return subprocess.run([sys.executable,"-c","from app.main import app; print('/api/lab/orders/{order_id}' in app.openapi()['paths'])"],env=env,capture_output=True,text=True)

def test_lab_fixture_can_be_enabled_but_stays_out_of_schema():
    result=run_import("127.0.0.1");assert result.returncode==0;assert result.stdout.strip()=="False"

def test_lab_route_callable_in_isolated_enabled_process():
    env=os.environ.copy();env.update({"LAB_VULNERABILITIES_ENABLED":"true","HOST":"127.0.0.1","DATABASE_URL":"sqlite:///./lab-test.db"})
    code="from app.main import app; from app.database import Base,engine,SessionLocal; from scripts.seed_data import seed; from fastapi.testclient import TestClient; Base.metadata.create_all(engine); db=SessionLocal(); seed(db); db.close(); c=TestClient(app); token=c.post('/api/v1/auth/login',json={'email':'alice@example.com','password':'Password123!'}).json()['access_token']; r=c.get('/api/lab/orders/4',headers={'Authorization':'Bearer '+token}); print(r.status_code, r.json().get('customer_id'))"
    result=subprocess.run([sys.executable,"-c",code],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip().endswith("200 2")

def test_lab_fixture_refuses_non_loopback_host():
    result=run_import("0.0.0.0");assert result.returncode!=0;assert "requires a loopback host" in result.stderr
