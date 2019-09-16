# General
PROJECT_CODE = "waqtec"
COMMON_TAGS = {
    "ProjectCode": PROJECT_CODE,
    "Environment": "prod",
    "Owner": "mwaqqas"
}

# Route53
# For CREATING a Hosted Zone:
#   Leave "id" as empty "" if you want to create a hosted zone
#   Insert values for "name" and "domain"
# For IMPORTING a Pre-existing Hosted Zone:
#   Insert values for "id", "name", and "domain"
HOSTED_ZONE = {
    "id": "Z37WEOKUCYC5ME",
    "name": "waqqas.tech",
    "domain": "waqqas.tech",
}
# CERTIFICATE
# For CREATING an ACM Certificate:
#   Leave "arn" as empty "" if you want to create an ACM certificate
#   Insert values for "alt_domains" and "region"
# For IMPORTING a Pre-existing ACM Certificate:
#   Insert value of "arn"
#   Leave "alt_domain" and "region" as empty
CERTIFICATE = {
    "arn": "arn:aws:acm:us-east-1:147218828400:certificate/2e249ec4-2a86-4cc4-a535-ee01f7ba6842",
    "alt_domains": [
        "*.waqqas.tech"
    ],
    "region": "us-east-1",
}

# CloudFront Variables
CLOUDFRONT = {
    "alt_domains": [
        "waqqas.tech",
        "blog.waqqas.tech"
    ],
    "default_ttl": 60,
}
