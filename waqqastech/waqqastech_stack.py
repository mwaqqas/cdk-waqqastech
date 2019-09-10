from aws_cdk import core
from aws_cdk import aws_s3, aws_iam, aws_cloudfront
from aws_cdk import aws_route53, aws_route53_targets
from aws_cdk import aws_certificatemanager
from constants import *


class WaqqastechStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Common Stack Tags
        for k, v in COMMON_TAGS.items():
            core.Tag.add(self, key=k, value=v)

        # Hosted Zone
        hosted_zone = aws_route53.HostedZone(
            self,
            "MainHostedZone",
            zone_name=HOSTED_ZONE_NAME,
            comment="Hosted Zone for {}".format(HOSTED_ZONE_NAME),
        )

        # ACM Certificate
        # This Construct (DnsValidatedCertificate) creates a few Custom Resources
        # Therefore, the dependancy on Hosted Zone needs to be explicitly declared
        # in order to delete the stack properly
        acm_certificate = aws_certificatemanager.DnsValidatedCertificate(
            self,
            "CloudFrontCertificate",
            hosted_zone=hosted_zone,
            region=CERTIFICATE_REGION,
            domain_name=DOMAIN_NAME,
            subject_alternative_names=CERTIFICATE_ALT_DOMAIN_NAMES,
            validation_method=aws_certificatemanager.ValidationMethod.DNS
        )

        acm_certificate.node.add_dependency(hosted_zone)

        # Website Bucket
        website_bucket = aws_s3.Bucket(
            self,
            "WebsiteBucket",
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Cloudfront Origin Access Identity (OAI)
        website_bucket_oai = aws_cloudfront.CfnCloudFrontOriginAccessIdentity(
            self,
            "CloudfrontOAI",
            cloud_front_origin_access_identity_config=aws_cloudfront.CfnCloudFrontOriginAccessIdentity.CloudFrontOriginAccessIdentityConfigProperty(
                comment="CloudFrontOAIFor{}".format(PROJECT_CODE.capitalize())
            )
        )

        # Canonical User Principal of OAI
        oai_canonical_user_principal = aws_iam.CanonicalUserPrincipal(
            website_bucket_oai.attr_s3_canonical_user_id
        )

        # Website Bucket Policy
        website_bucket.add_to_resource_policy(
            aws_iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[website_bucket.arn_for_objects("*")],
                principals=[oai_canonical_user_principal],
                effect=aws_iam.Effect.ALLOW
            )
        )

        # CloudFront Web Distribution
        cloudfront_distribution = aws_cloudfront.CloudFrontWebDistribution(
            self,
            "CloudFrontDistribution",
            comment="waqqas.tech",
            default_root_object="index.html",
            viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            alias_configuration=aws_cloudfront.AliasConfiguration(
                acm_cert_ref=acm_certificate.certificate_arn,
                security_policy=aws_cloudfront.SecurityPolicyProtocol.TLS_V1_2_2018,
                names=CLOUDFRONT_DIST_ALT_DOMAINS
            ),
            origin_configs=[
                aws_cloudfront.SourceConfiguration(
                    s3_origin_source=aws_cloudfront.S3OriginConfig(
                        s3_bucket_source=website_bucket,
                        origin_access_identity_id=website_bucket_oai.ref
                    ),
                    behaviors=[
                        aws_cloudfront.Behavior(
                            allowed_methods=aws_cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                            cached_methods=aws_cloudfront.CloudFrontAllowedCachedMethods.GET_HEAD,
                            compress=True,
                            is_default_behavior=True,
                            path_pattern="*",
                            default_ttl=core.Duration.seconds(amount=60),
                        )
                    ]
                )
            ]
        )

        # CloudFront Route53 Record
        apex_domain_dns_record = aws_route53.ARecord(
            self,
            "PrimaryAliasDNSRecord",
            zone=hosted_zone,
            comment="{} CloudFront Dist Alias Record".format(PROJECT_CODE),
            record_name="{}.".format(DOMAIN_NAME),
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.CloudFrontTarget(
                    cloudfront_distribution
                )
            ),
            ttl=core.Duration.seconds(amount=CLOUDFRONT_DEFAULT_TTL),
        )
