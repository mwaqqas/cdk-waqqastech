from aws_cdk import core
from aws_cdk import aws_s3, aws_iam, aws_cloudfront
from aws_cdk import aws_route53, aws_route53_targets
from aws_cdk import aws_certificatemanager
from aws_cdk import aws_codebuild
import constants
import buildspec


class WaqqastechStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # super().__init__(scope, id, context, outdir)

        print()
        # Common Stack Tags
        for k, v in constants.COMMON_TAGS.items():
            core.Tag.add(self, key=k, value=v)

        # Hosted Zone
        if constants.HOSTED_ZONE["id"]:
            hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(
                self,
                "ImportedHostedZone",
                hosted_zone_id=constants.HOSTED_ZONE["id"],
                zone_name=constants.HOSTED_ZONE["name"]
            )
        else:
            hosted_zone = aws_route53.HostedZone(
                self,
                "MainHostedZone",
                zone_name=constants.HOSTED_ZONE["name"],
                comment="Hosted Zone for {}".format(constants.HOSTED_ZONE["name"]),
            )

        # ACM Certificate
        if constants.CERTIFICATE["arn"]:
            acm_certificate = aws_certificatemanager.Certificate.from_certificate_arn(
                self,
                "ImportedCertificate",
                certificate_arn=constants.CERTIFICATE["arn"]
            )
        else:
            acm_certificate = aws_certificatemanager.DnsValidatedCertificate(
                self,
                "CloudFrontCertificate",
                hosted_zone=hosted_zone,
                region=constants.CERTIFICATE["region"],
                domain_name=constants.HOSTED_ZONE["domain"],
                subject_alternative_names=constants.CERTIFICATE["alt_domains"],
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
            cloud_front_origin_access_identity_config=aws_cloudfront
            .CfnCloudFrontOriginAccessIdentity
            .CloudFrontOriginAccessIdentityConfigProperty(
                comment="CloudFrontOAIFor{}".format(
                    constants.PROJECT_CODE.capitalize()
                )
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
            viewer_protocol_policy=aws_cloudfront
            .ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            alias_configuration=aws_cloudfront.AliasConfiguration(
                acm_cert_ref=acm_certificate.certificate_arn,
                security_policy=aws_cloudfront
                .SecurityPolicyProtocol.TLS_V1_2_2018,
                names=constants.CLOUDFRONT["alt_domains"]
            ),
            origin_configs=[
                aws_cloudfront.SourceConfiguration(
                    s3_origin_source=aws_cloudfront.S3OriginConfig(
                        s3_bucket_source=website_bucket,
                        origin_access_identity_id=website_bucket_oai.ref
                    ),
                    behaviors=[
                        aws_cloudfront.Behavior(
                            allowed_methods=aws_cloudfront
                            .CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                            cached_methods=aws_cloudfront
                            .CloudFrontAllowedCachedMethods.GET_HEAD,
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
        primary_dns_record = aws_route53.ARecord(
            self,
            "PrimaryDNSRecord",
            zone=hosted_zone,
            comment="{} CloudFront Dist Alias Record".format(constants.PROJECT_CODE),
            record_name="{}.".format(constants.HOSTED_ZONE["domain"]),
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.CloudFrontTarget(
                    cloudfront_distribution
                )
            ),
            ttl=core.Duration.seconds(amount=constants.CLOUDFRONT["default_ttl"]),
        )

        # Artifact Bucket
        artifact_bucket = aws_s3.Bucket(
            self,
            "ArtifactBucket",
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # CodeBuild
        codebuild_environment_variables = aws_codebuild.BuildEnvironmentVariable(
            value=website_bucket.bucket_name
        )
        codebuild_environment = aws_codebuild.BuildEnvironment(
            build_image=aws_codebuild.LinuxBuildImage.UBUNTU_14_04_PYTHON_3_7_1,
            compute_type=aws_codebuild.ComputeType.SMALL
        )
        codebuild_buildspec = aws_codebuild.BuildSpec.from_object(
            value=buildspec.BUILDSPEC
        )
        codebuild_project = aws_codebuild.PipelineProject(
            self,
            "CodeBuildProject",
            environment_variables={
                "BUCKET_NAME": codebuild_environment_variables
            },
            environment=codebuild_environment,
            build_spec=codebuild_buildspec,
            description="CodeBuild Project for {} Content".format(constants.PROJECT_CODE),
            timeout=core.Duration.seconds(amount=180)
        )

        # Codepipeline
