from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema_view
)
from .docstring import *
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer

request_otp_docs = extend_schema(
    summary="Generate and send OTP to user's phone number",
    description=GENERATE_OTP_DESC,
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={"number": "+989123456789"},
            request_only=True,
            description="Standard Iranian mobile number format"
        ),
        OpenApiExample(
            name="Invalid Request",
            value={"number": "09123456789"},
            request_only=True,
            description="Missing country code prefix"
        )
    ],
    parameters=[
        OpenApiParameter(
            name="number",
            description="Phone number in international format",
            required=True,
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[
                OpenApiExample(
                    "Valid Example",
                    value="+989123456789",
                    description="Iranian mobile number with country code"
                )
            ]
        )
    ],
    responses={
        201: OpenApiResponse(
            description="OTP Sent Successfully",
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        "message": "OTP sent successfully",
                        "created": True
                    }
                )
            ]
        ),
        200: OpenApiResponse(
            description="OTP Resent",
            examples=[
                OpenApiExample(
                    'Resend Response',
                    value={
                        "message": "OTP sent successfully",
                        "created": False
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid Request",
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={"number": ["Enter a valid phone number"]}
                )
            ]
        )
    },
    tags=["Authentication"],
    methods=["POST"]
)

verify_otp_docs = extend_schema(
    summary="Verify OTP and authenticate user",
    description=VERIFY_OTP_DESC,
    examples=[
        OpenApiExample(
            'Valid Request',
            value={"number": "+989123456789", "otp": 123456},
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Verification Successful",
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        "message": "User verified successfully",
                        "is_new": False,
                        "phone": "+989123456789",
                        "full_name": "John Doe"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Verification Failed",
            examples=[
                OpenApiExample(
                    'Invalid OTP',
                    value={"otp": ["Invalid OTP provided"]}
                ),
                OpenApiExample(
                    'Invalid Number',
                    value={"number": ["User not found"]}
                )
            ]
        )
    },
    tags=["Authentication"],
    methods=["POST"]
)

refresh_token_docs = extend_schema(
    summary="Refresh JWT tokens",
    description=REFRESH_TOKEN_DESC,
    responses={
        200: OpenApiResponse(
            description="Token Refresh Successful",
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        "access": "new_access_token",
                        "refresh": "new_refresh_token"
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description="Invalid Token",
            examples=[
                OpenApiExample(
                    'Invalid Token',
                    value={"detail": "Token is invalid or expired"}
                )
            ]
        )
    },
    tags=["Authentication"],
    methods=["POST"]
)

logout_docs = extend_schema(
    summary="Invalidate refresh token",
    description=LOGOUT_DESC,
    responses={
        200: OpenApiResponse(
            description="Logout Successful",
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={"message": "Successfully logged out"}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Unauthorized",
            examples=[
                OpenApiExample(
                    'Invalid Token',
                    value={"detail": "Authentication credentials were not provided."}
                )
            ]
        )
    },
    tags=["Authentication"],
    methods=["POST"]
)

user_profile_viewset_docs = extend_schema_view(
    retrieve=extend_schema(
        operation_id="user_profile_retrieve",
        summary="Get User Profile",
        description=USER_PROFILE_RETRIEVE_DESC,
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    "first_name": "John",
                    "last_name": "Doe",
                    "bio": "Software Developer",
                    "job": "Backend Engineer",
                    "avatar": "/media/avatars/user123.jpg",
                    "avatar_thumbnail": "/media/avatars/thumbnails/user123.jpg",
                    "age": 30,
                    "gender": "M",
                    "phone": "+989123456789",
                    "email": "john.doe@example.com"
                },
                response_only=True,
                status_codes=['200']
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Profile retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "bio": {"type": "string"},
                        "job": {"type": "string"},
                        "avatar": {"type": "string"},
                        "avatar_thumbnail": {"type": "string"},
                        "age": {"type": "integer"},
                        "gender": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[
                    OpenApiExample(
                        'Error',
                        value={"detail": "Authentication credentials were not provided"}
                    )
                ]
            )
        },
        tags=["User Profile"]
    ),
    partial_update=extend_schema(
        operation_id="user_profile_update",
        summary="Update User Profile",
        description=USER_PROFILE_UPDATE_DESC,
        examples=[
            OpenApiExample(
                'Request Example',
                value={
                    "first_name": "John",
                    "last_name": "Smith",
                    "bio": "Updated bio",
                    "job": "Senior Backend Engineer"
                },
                request_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Success Response',
                value={
                    "first_name": "John",
                    "last_name": "Smith",
                    "bio": "Updated bio",
                    "job": "Senior Backend Engineer",
                    "avatar": "/media/avatars/user123.jpg",
                    "avatar_thumbnail": "/media/avatars/thumbnails/user123.jpg",
                    "age": 30,
                    "gender": "M",
                    "phone": "+989123456789",
                    "email": "john.doe@example.com"
                },
                response_only=True,
                status_codes=['200']
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Profile updated successfully",
                response={
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "bio": {"type": "string"},
                        "job": {"type": "string"},
                        "avatar": {"type": "string"},
                        "avatar_thumbnail": {"type": "string"},
                        "age": {"type": "integer"},
                        "gender": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            ),
            400: OpenApiResponse(
                description="Validation Error",
                examples=[
                    OpenApiExample(
                        'Error',
                        value={
                            "last_name": ["This field is required"],
                            "avatar": ["Invalid file format"]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[
                    OpenApiExample(
                        'Error',
                        value={"detail": "Authentication credentials were not provided"}
                    )
                ]
            )
        },
        tags=["User Profile"]
    )
)

change_phone_request_docs = extend_schema(
    summary="Request phone number change",
    description=CHANGE_PHONE_REQUEST_DESC,
    examples=[
        OpenApiExample(
            'Valid Request',
            value={"phone": "+989123456789"},
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(
            description="OTP sent successfully"
        ),
        400: OpenApiResponse(
            description="Invalid phone number format or already registered"
        ),
        403: OpenApiResponse(
            description="Rate limit exceeded"
        )
    },
    tags=["User Profile"],
    methods=["POST"]
)

change_phone_verify_docs = extend_schema(
    summary="Verify phone number change",
    description=CHANGE_PHONE_VERIFY_DESC,
    examples=[
        OpenApiExample(
            'Valid Request',
            value={"phone": "+989123456789", "otp": 123456},
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Phone number changed successfully"
        ),
        400: OpenApiResponse(
            description="Invalid OTP or expired"
        )
    },
    tags=["User Profile"],
    methods=["POST"]
)

change_email_request_docs = extend_schema(
    summary="Request email change",
    description=CHANGE_EMAIL_REQUEST_DESC,
    examples=[
        OpenApiExample(
            'Valid Request',
            value={"email": "new.email@example.com"},
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Verification email sent"
        ),
        400: OpenApiResponse(
            description="Invalid email or already registered"
        )
    },
    tags=["User Profile"],
    methods=["POST"]
)

change_email_verify_docs = extend_schema(
    summary="Verify email change",
    description=CHANGE_PHONE_VERIFY_DESC,
    parameters=[
        OpenApiParameter(
            name="email_verify_token",
            type=str,
            location=OpenApiParameter.PATH
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Email updated successfully"
        ),
        400: OpenApiResponse(
            description="Invalid or expired token"
        )
    },
    tags=["User Profile"],
    methods=["GET"]
)
