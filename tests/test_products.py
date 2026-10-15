def test_product_list_search_filters_and_pagination(client):
    assert len(client.get("/api/v1/products?page=1&page_size=4").json())==4
    assert len(client.get("/api/v1/products?category=Ringer%20Tees&min_price=800&max_price=950").json())>=1
    assert client.get("/api/v1/products?min_price=90&max_price=10").status_code==422
    assert len(client.get("/api/v1/products/search?q=acid%20wash").json())>=1
    assert len(client.get("/api/v1/products/featured").json())>=1
    assert client.get("/api/v1/products/1/reviews").status_code==200
    assert client.get("/api/v1/products/9999").status_code==404
def test_lab_fixture_and_exact_tags(client):
    paths=client.get("/openapi.json").json()["paths"]
    assert "/api/lab/orders/{order_id}" not in paths
    assert {tag["name"] for tag in client.get("/openapi.json").json()["tags"]}=={"Customers","Authentication","Orders","Products"}
