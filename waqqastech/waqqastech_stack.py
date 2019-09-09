from aws_cdk import core
from aws_cdk import aws_s3, aws_iam, aws_cloudfront, aws_route53
from aws_cdk import aws_certificatemanager


class WaqqastechStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Hosted Zone
        hosted_zone = aws_route53.HostedZone(
            self,
            "ApexHostedZone",
            zone_name="waqqas.tech",
            comment="waqqas.tech",
        )

        # ACM Certificate
        # acm_certificate = aws_certificatemanager.DnsValidatedCertificate(
        #     self,
        #     "CloudFrontCertificate",
        #     hosted_zone=hosted_zone,
        #     region="us-east-1",
        #     domain_name="waqqas.tech.",
        #     subject_alternative_names=[
        #         "blog.waqqas.tech"
        #     ],
        #     validation_method=aws_certificatemanager.ValidationMethod.DNS
        # )

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
                comment="abc"
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
        # cloudfront_distribution = aws_cloudfront.CloudFrontWebDistribution(
        #     self,
        #     "CloudFrontDistribution",
        #     comment="This is a comment",
        #     default_root_object="index.html",
        #     viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        #     alias_configuration=aws_cloudfront.AliasConfiguration(
        #         acm_cert_ref="arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012",
        #         security_policy=aws_cloudfront.SecurityPolicyProtocol.TLS_V1_2_2018,
        #         names=[
        #             "waqqas.tech",
        #             "blog.waqqas.tech"
        #         ]
        #     ),
        #     origin_configs=[
        #         aws_cloudfront.SourceConfiguration(
        #             s3_origin_source=aws_cloudfront.S3OriginConfig(
        #                 s3_bucket_source=website_bucket,
        #                 origin_access_identity_id=website_bucket_oai.attr_s3_canonical_user_id
        #             ),
        #             origin_path="/",
        #             behaviors=[
        #                 aws_cloudfront.Behavior(
        #                     allowed_methods=aws_cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
        #                     cached_methods=aws_cloudfront.CloudFrontAllowedCachedMethods.GET_HEAD,
        #                     compress=True,
        #                     is_default_behavior=True,
        #                     path_pattern="*",
        #                     default_ttl=core.Duration.seconds(amount=3600),
        #                 )
        #             ]
        #         )
        #     ]
        # )
