from app.models.user import ROLE_ADMIN,User

def test_register_user(client):

    response = client.post("/users/register",json={
    "email":"test@example.com",
    "password":"secret123",})

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["email"] == "test@example.com"
    assert response_data["is_active"] is True
    assert "id" in response_data
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert "password" not in response_data
    assert "hashed_password" not in response_data


def test_register_user_with_duplicate_email(client):
    user_data = {
        "email":"duplicate@example.com",
        "password":"secret123"
    }

    first_response = client.post("/users/register",json=user_data)

    second_response = client.post("/users/register",json=user_data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    assert second_response.json()=={"detail":"User With This Email Already Exists"}

def test_register_user_with_invalid_mail(client):
    response=client.post("/users/register",json={"email":"not-an-email","password":"secret123"})

    assert response.status_code==422

def test_register_user_with_short_password(client):
    response=client.post("/users/register",json={"email":"test@example.com","password":"123"})

    assert response.status_code==422

def register_auth_user(client,email="auth@example.com",password="secret123"):
    response = client.post("/users/register",json={"email": email,"password": password})

    assert response.status_code == 201

    return response.json()

def test_login_returns_access_token(client):
    register_auth_user(client)

    response = client.post("/users/login",json={"email": "auth@example.com","password": "secret123"})

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["token_type"] == "bearer"
    assert isinstance(response_data["access_token"],str)
    assert response_data["access_token"]

def test_login_with_wrong_password(client):
    register_auth_user(client)

    response = client.post("/users/login",json={"email": "auth@example.com","password": "wrong-password"})

    assert response.status_code == 401

    assert response.json() == {"detail": "Invalid email or password"}

    assert response.headers["www-authenticate"] == "Bearer"

def test_login_with_unknown_email(client):
    response = client.post("/users/login",json={"email": "unknown@example.com","password": "secret123"})

    assert response.status_code == 401

    assert response.json() == {"detail": "Invalid email or password"}

def test_get_me_without_token_returns_401(client):
    response = client.get("/users/me")

    assert response.status_code == 401

    assert response.json() == {"detail": "Invalid or expired access token"}

def test_get_me_with_valid_token(client):
    registered_user = register_auth_user(client)

    login_response = client.post("/users/login",json={"email": "auth@example.com","password": "secret123"})

    token = login_response.json()["access_token"]

    response = client.get("/users/me",headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == registered_user["id"]
    assert response_data["email"] == "auth@example.com"
    assert response_data["role"] == "employee"

def test_get_me_with_invalid_token_returns_401(client):
    response = client.get("/users/me",headers={"Authorization":"Bearer this-is-not-a-valid-jwt"})

    assert response.status_code == 401

    assert response.json() == {"detail": "Invalid or expired access token"}

def test_employee_cannot_access_admin_endpoint(client):
    from app.main import app
    from app.dependencies.auth import require_admin
    app.dependency_overrides.pop(require_admin,None)
    register_auth_user(client)

    login_response = client.post("/users/login",json={"email": "auth@example.com","password": "secret123"})

    token = login_response.json()["access_token"]

    response = client.get("/users/admin-check",headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403

    assert response.json() == {"detail": "Admin permission required"}

def test_admin_can_access_admin_endpoint(client,db_session):
    registered_user = register_auth_user(client,email="admin@example.com")

    user = db_session.get(User,registered_user["id"])

    user.role = ROLE_ADMIN
    db_session.commit()

    login_response = client.post("/users/login",json={"email": "admin@example.com","password": "secret123"})

    token = login_response.json()["access_token"]

    response = client.get("/users/admin-check",headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200

    assert response.json() == {"message": "Admin access granted","user_id": registered_user["id"]}
