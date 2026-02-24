from django.urls import reverse

from utils.test import *


class AuthenticationTests(WebAppAPITestCase):
    base_url = reverse("authentication:main")
    test_cases: list[APITestCasePack] = [
        APITestCasePack(
            title="Send Verification Code",
            method="GET",
            auth_required=False,
            cases=[
                APITestCaseModel(
                    input={"mobile": "09991234567"},
                    output={"has_password": False},
                    expected_code=200,
                ),
                APITestCaseModel(
                    input={"mobile": "invalid"},
                    output={"devMessages": {"mobile": ["Must be a standard mobile like 0910*******."]}},
                    expected_code=400,
                ),
                APITestCaseModel(
                    input={},
                    output={"devMessages": {"mobile": ["This field is required."]}},
                    expected_code=400,
                ),
            ],
        ),
        APITestCasePack(
            title="Login Or Register - Validation Failures",
            method="POST",
            auth_required=False,
            cases=[
                APITestCaseModel(
                    input={"mobile": "09991234567"},
                    output={"message": "اطلاعات ورود نامعتبر است."},
                    expected_code=400,
                ),
                APITestCaseModel(
                    input={"mobile": "invalid"},
                    output={"devMessages": {"mobile": ["Must be a standard mobile like 0910*******."]}},
                    expected_code=400,
                ),
                APITestCaseModel(
                    input={"mobile": "09991234567", "verification_code": "abc"},
                    output={"devMessages": {"verification_code": ["Must be 5 digits"]}},
                    expected_code=400,
                ),
            ],
        ),
        APITestCasePack(
            title="Update User Info",
            method="PUT",
            auth_required=True,
            cases=[
                APITestCaseModel(
                    input={"name": "علی رضایی"},
                    output={},
                    expected_code=200,
                ),
                APITestCaseModel(
                    input={"name": "Invalid Name 123"},
                    output={"devMessages": {"name": ["Must be all Persian letters. It must not contain any numbers or symbols."]}},
                    expected_code=400,
                ),
            ],
        ),
        APITestCasePack(
            title="Logout",
            method="DELETE",
            auth_required=True,
            cases=[
                APITestCaseModel(
                    input={},
                    output={},
                    expected_code=200,
                ),
            ],
        ),
    ]

    def setUp(self):
        self.base_setUp()

    def test_cases_run(self):
        self.run_tests()


class PasswordTests(WebAppAPITestCase):
    base_url = reverse("authentication:password")
    test_cases: list[APITestCasePack] = [
        APITestCasePack(
            title="Send Verification Code For Password",
            method="GET",
            auth_required=True,
            cases=[
                APITestCaseModel(
                    input={},
                    output={},
                    expected_code=200,
                ),
            ],
        ),
        APITestCasePack(
            title="Verify Code For Password - Wrong Code",
            method="POST",
            auth_required=True,
            cases=[
                APITestCaseModel(
                    input={"verification_code": "00000"},
                    output={"message": "کد تایید نامعتبر است."},
                    expected_code=400,
                ),
            ],
        ),
        APITestCasePack(
            title="Disable Password",
            method="DELETE",
            auth_required=True,
            cases=[
                APITestCaseModel(
                    input={},
                    output={},
                    expected_code=200,
                ),
            ],
        ),
    ]

    def setUp(self):
        self.base_setUp()

    def test_cases_run(self):
        self.run_tests()
