def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@markflow.local",
            "password": "secretpassword",
            "full_name": "New User",
            "role": "STUDENT"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@markflow.local"
    assert data["role"] == "STUDENT"
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@markflow.local",
        "password": "secretpassword",
        "full_name": "First User",
        "role": "TUTOR"
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]


def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@markflow.local", "password": "mypassword", "role": "STUDENT"}
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@markflow.local", "password": "mypassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "STUDENT"


def test_login_invalid_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "badpwd@markflow.local", "password": "correct", "role": "STUDENT"}
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "badpwd@markflow.local", "password": "wrongpassword"}
    )
    assert response.status_code == 401
