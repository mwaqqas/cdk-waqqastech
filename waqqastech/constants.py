# General
PROJECT_CODE = "waqtec"
COMMON_TAGS = {
    "ProjectCode": PROJECT_CODE,
    "Environment": "prod",
    "Owner": "mohamed.waqqas"
}

# Route53
HOSTED_ZONE_NAME = "waqqas.tech"
DOMAIN_NAME = "waqqas.tech"

# Certificate
CERTIFICATE_ALT_DOMAIN_NAMES = [
    "*.waqqas.tech"
]
CERTIFICATE_REGION = "us-east-1"

# CloudFront
CLOUDFRONT_DIST_ALT_DOMAINS = [
    "waqqas.tech",
    "blog.waqqas.tech"
]
CLOUDFRONT_DEFAULT_TTL = 60
