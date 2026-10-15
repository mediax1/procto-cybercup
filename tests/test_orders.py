def test_order_create_ownership_cancel_and_tracking(client,alice_token):
    h={"Authorization":f"Bearer {alice_token}"}
    created=client.post("/api/v1/orders",headers=h,json={"items":[{"product_id":1,"quantity":1}],"shipping_address":"12 Willow Lane, Portland, OR 97205"});assert created.status_code==201
    oid=created.json()["id"];assert client.get(f"/api/v1/orders/{oid}",headers=h).status_code==200
    bob=client.post("/api/v1/auth/login",json={"email":"bob@example.com","password":"Password123!"}).json()["access_token"]
    assert client.get(f"/api/v1/orders/{oid}",headers={"Authorization":f"Bearer {bob}"}).status_code==403
    assert client.get(f"/api/v1/orders/{oid}/tracking",headers=h).status_code==200
    assert client.post(f"/api/v1/orders/{oid}/cancel",headers=h).status_code==200
    assert client.post(f"/api/v1/orders/{oid}/cancel",headers=h).status_code==409
def test_patch_rejects_protected_fields(client,alice_token):
    h={"Authorization":f"Bearer {alice_token}"}
    assert client.patch("/api/v1/orders/1",headers=h,json={"customer_id":2}).status_code==422
