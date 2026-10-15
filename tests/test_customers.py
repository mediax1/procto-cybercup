def test_profile_and_address_ownership(client,alice_token):
    h={"Authorization":f"Bearer {alice_token}"}
    me=client.get("/api/v1/customers/me",headers=h);assert me.status_code==200
    assert client.patch("/api/v1/customers/me",headers=h,json={"name":"Alice New"}).json()["name"]=="Alice New"
    assert client.get("/api/v1/customers/2",headers=h).status_code==403
    theirs=client.get("/api/v1/customers/me/addresses",headers={"Authorization":"Bearer "+client.post("/api/v1/auth/login",json={"email":"bob@example.com","password":"Password123!"}).json()["access_token"]}).json()[0]
    assert client.patch(f"/api/v1/customers/me/addresses/{theirs['id']}",headers=h,json={"label":"Mine"}).status_code==403
    created=client.post("/api/v1/customers/me/addresses",headers=h,json={"line1":"1 Test Street","city":"Austin","region":"Texas","postal_code":"78701"});assert created.status_code==201
    assert client.delete(f"/api/v1/customers/me/addresses/{created.json()['id']}",headers=h).status_code==204
