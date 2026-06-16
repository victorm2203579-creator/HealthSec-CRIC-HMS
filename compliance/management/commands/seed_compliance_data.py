"""
compliance/management/commands/seed_compliance_data.py
=======================================================
Populates the database with realistic compliance frameworks and controls,
then runs an initial automated check to generate baseline results.

Creates:
  - HIPAA framework with 15 controls
  - NDPR framework  with 10 controls
  - ISO 27001 framework with 12 controls
  - Initial automated compliance check results for all controls

Usage::

    python manage.py seed_compliance_data
    python manage.py seed_compliance_data --clear    # wipe data first
    python manage.py seed_compliance_data --no-check  # skip initial run
"""

from django.core.management.base import BaseCommand

from compliance.checker import ComplianceChecker
from compliance.models import ComplianceControl, ComplianceFramework


# ---------------------------------------------------------------------------
# Framework & control definitions
# ---------------------------------------------------------------------------

FRAMEWORKS = [
    {
        'name': 'Health Insurance Portability and Accountability Act',
        'short_name': 'HIPAA',
        'version': '2013 Omnibus Rule',
        'issuing_body': 'U.S. Department of Health & Human Services',
        'applicable_region': 'USA',
        'description': (
            'Federal law requiring protection and confidential handling of '
            'protected health information (PHI). Applies to covered entities '
            'and their business associates.'
        ),
        'controls': [
            {
                'control_code': 'HIPAA-164.308(a)(1)',
                'title': 'Risk Management',
                'description': 'Implement policies and procedures to prevent, detect, contain, and correct security violations through risk analysis and management.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_access_control',
            },
            {
                'control_code': 'HIPAA-164.308(a)(3)',
                'title': 'Workforce Security',
                'description': 'Implement procedures to ensure appropriate access authorisation, workforce clearance, and termination procedures.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 0.9,
                'automated_check': True,
                'check_function_name': 'check_access_control',
            },
            {
                'control_code': 'HIPAA-164.308(a)(4)',
                'title': 'Access Management',
                'description': 'Implement policies for authorising access to ePHI based on role and need-to-know.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_access_control',
            },
            {
                'control_code': 'HIPAA-164.308(a)(5)',
                'title': 'Security Awareness Training',
                'description': 'Implement a security awareness and training programme for all workforce members.',
                'control_category': 'TRAINING',
                'weight': 0.8,
                'automated_check': True,
                'check_function_name': 'check_user_training_records',
            },
            {
                'control_code': 'HIPAA-164.308(a)(6)',
                'title': 'Security Incident Procedures',
                'description': 'Implement policies to address security incidents, including reporting and response procedures.',
                'control_category': 'INCIDENT_RESPONSE',
                'weight': 0.95,
                'automated_check': True,
                'check_function_name': 'check_incident_response',
            },
            {
                'control_code': 'HIPAA-164.308(a)(7)',
                'title': 'Contingency Plan & Data Backup',
                'description': 'Establish and implement procedures to respond to emergencies and ensure data backup.',
                'control_category': 'DATA_BACKUP',
                'weight': 0.85,
                'automated_check': True,
                'check_function_name': 'check_data_backup_policy',
            },
            {
                'control_code': 'HIPAA-164.310(a)(1)',
                'title': 'Facility Access Controls',
                'description': 'Implement policies to limit physical access to electronic information systems to authorised users.',
                'control_category': 'PHYSICAL_SECURITY',
                'weight': 0.7,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'HIPAA-164.312(a)(1)',
                'title': 'Unique User Identification',
                'description': 'Assign a unique name and/or number for identifying and tracking user identity.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 0.9,
                'automated_check': True,
                'check_function_name': 'check_access_control',
            },
            {
                'control_code': 'HIPAA-164.312(a)(2)(iii)',
                'title': 'Automatic Logoff',
                'description': 'Implement electronic procedures that terminate sessions after a defined period of inactivity.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 0.85,
                'automated_check': True,
                'check_function_name': 'check_session_timeout',
            },
            {
                'control_code': 'HIPAA-164.312(a)(2)(iv)',
                'title': 'Encryption and Decryption',
                'description': 'Implement a mechanism to encrypt and decrypt ePHI.',
                'control_category': 'ENCRYPTION',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_encryption_status',
            },
            {
                'control_code': 'HIPAA-164.312(b)',
                'title': 'Audit Controls',
                'description': 'Implement hardware, software, and/or procedural mechanisms that record and examine activity in systems containing ePHI.',
                'control_category': 'AUDIT_LOGGING',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_audit_logging',
            },
            {
                'control_code': 'HIPAA-164.312(d)',
                'title': 'Person/Entity Authentication',
                'description': 'Implement procedures to verify that a person seeking access to ePHI is the one claimed.',
                'control_category': 'PASSWORD_POLICY',
                'weight': 0.9,
                'automated_check': True,
                'check_function_name': 'check_password_policy',
            },
            {
                'control_code': 'HIPAA-164.312(e)(1)',
                'title': 'Transmission Security',
                'description': 'Implement technical security measures to guard against unauthorised access to ePHI transmitted over networks.',
                'control_category': 'NETWORK_SECURITY',
                'weight': 0.9,
                'automated_check': True,
                'check_function_name': 'check_encryption_status',
            },
            {
                'control_code': 'HIPAA-164.308(a)(8)',
                'title': 'Failed Login Monitoring',
                'description': 'Implement procedures to monitor login activity and detect repeated authentication failures.',
                'control_category': 'AUDIT_LOGGING',
                'weight': 0.85,
                'automated_check': True,
                'check_function_name': 'check_failed_login_monitoring',
            },
            {
                'control_code': 'HIPAA-164.316(b)(1)',
                'title': 'Documentation',
                'description': 'Implement policies and procedures to comply with HIPAA and maintain written records of these policies.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 0.6,
                'automated_check': False,
                'check_function_name': '',
            },
        ],
    },
    {
        'name': 'Nigeria Data Protection Regulation',
        'short_name': 'NDPR',
        'version': '2019',
        'issuing_body': 'National Information Technology Development Agency (NITDA)',
        'applicable_region': 'Nigeria',
        'description': (
            'Nigerian data protection regulation governing the collection, '
            'storage, processing, and management of personal data of Nigerian '
            'citizens and residents.'
        ),
        'controls': [
            {
                'control_code': 'NDPR-1.1',
                'title': 'Data Controller Registration',
                'description': 'Register as a data controller with NITDA and submit annual data protection audit report.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 1.0,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'NDPR-2.1',
                'title': 'Lawful Basis for Processing',
                'description': 'Ensure all personal data processing has a valid legal basis (consent, contract, legal obligation, vital interests, public task, or legitimate interests).',
                'control_category': 'ACCESS_CONTROL',
                'weight': 0.95,
                'automated_check': True,
                'check_function_name': 'check_access_control',
            },
            {
                'control_code': 'NDPR-3.1',
                'title': 'Data Subject Rights',
                'description': 'Implement mechanisms to honour data subject rights: access, rectification, erasure, portability, and objection.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 0.9,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'NDPR-4.1',
                'title': 'Privacy Notice',
                'description': 'Provide clear, accessible privacy notices to data subjects at the point of data collection.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 0.8,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'NDPR-5.1',
                'title': 'Data Security Measures',
                'description': 'Implement appropriate technical and organisational measures to protect personal data against unauthorised access, loss, and destruction.',
                'control_category': 'ENCRYPTION',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_encryption_status',
            },
            {
                'control_code': 'NDPR-6.1',
                'title': 'Data Breach Notification',
                'description': 'Report data breaches to NITDA within 72 hours and notify affected data subjects without undue delay.',
                'control_category': 'INCIDENT_RESPONSE',
                'weight': 0.95,
                'automated_check': True,
                'check_function_name': 'check_incident_response',
            },
            {
                'control_code': 'NDPR-7.1',
                'title': 'Data Minimisation',
                'description': 'Collect only personal data that is adequate, relevant, and limited to what is necessary for the specified purpose.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 0.8,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'NDPR-8.1',
                'title': 'Data Retention Policy',
                'description': 'Establish and enforce retention schedules; delete personal data when no longer necessary for the original purpose.',
                'control_category': 'DATA_BACKUP',
                'weight': 0.75,
                'automated_check': True,
                'check_function_name': 'check_data_backup_policy',
            },
            {
                'control_code': 'NDPR-9.1',
                'title': 'Third Party / Processor Management',
                'description': 'Ensure data processors have appropriate contracts (Data Processing Agreements) and security measures in place.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 0.85,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'NDPR-10.1',
                'title': 'Cross-Border Data Transfer Controls',
                'description': 'Ensure personal data transferred outside Nigeria is protected to NDPR standards via adequacy decisions or appropriate safeguards.',
                'control_category': 'NETWORK_SECURITY',
                'weight': 0.9,
                'automated_check': False,
                'check_function_name': '',
            },
        ],
    },
    {
        'name': 'ISO/IEC 27001 Information Security Management',
        'short_name': 'ISO 27001',
        'version': '2022',
        'issuing_body': 'International Organization for Standardization (ISO)',
        'applicable_region': 'Global',
        'description': (
            'International standard specifying requirements for establishing, '
            'implementing, maintaining, and continually improving an information '
            'security management system (ISMS).'
        ),
        'controls': [
            {
                'control_code': 'ISO27001-A.5.1',
                'title': 'Information Security Policies',
                'description': 'Define, approve, publish, and communicate an information security policy and supporting policies.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 0.9,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'ISO27001-A.6.1',
                'title': 'Organisation of Information Security',
                'description': 'Assign security responsibilities, maintain contact with authorities, and address security in project management.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 0.8,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'ISO27001-A.7.1',
                'title': 'Human Resource Security',
                'description': 'Verify background of job candidates; ensure users understand their security responsibilities; enforce termination procedures.',
                'control_category': 'TRAINING',
                'weight': 0.85,
                'automated_check': True,
                'check_function_name': 'check_user_training_records',
            },
            {
                'control_code': 'ISO27001-A.8.1',
                'title': 'Asset Management',
                'description': 'Identify, classify, and manage information assets; establish acceptable use policies.',
                'control_category': 'RISK_MANAGEMENT',
                'weight': 0.75,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'ISO27001-A.9.1',
                'title': 'Access Control',
                'description': 'Implement access control policy; manage user access; control privileged access; review access rights regularly.',
                'control_category': 'ACCESS_CONTROL',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_access_control',
            },
            {
                'control_code': 'ISO27001-A.9.4',
                'title': 'Secure Logon & Session Management',
                'description': 'Implement secure log-on procedures; manage passwords; enforce session timeouts.',
                'control_category': 'PASSWORD_POLICY',
                'weight': 0.9,
                'automated_check': True,
                'check_function_name': 'check_session_timeout',
            },
            {
                'control_code': 'ISO27001-A.10.1',
                'title': 'Cryptography',
                'description': 'Implement policies for the use of cryptographic controls; manage cryptographic keys.',
                'control_category': 'ENCRYPTION',
                'weight': 0.95,
                'automated_check': True,
                'check_function_name': 'check_encryption_status',
            },
            {
                'control_code': 'ISO27001-A.11.1',
                'title': 'Physical and Environmental Security',
                'description': 'Implement physical security perimeters; protect against environmental threats; maintain secure equipment.',
                'control_category': 'PHYSICAL_SECURITY',
                'weight': 0.75,
                'automated_check': False,
                'check_function_name': '',
            },
            {
                'control_code': 'ISO27001-A.12.4',
                'title': 'Logging and Monitoring',
                'description': 'Record and monitor user activities, exceptions, faults, and information security events.',
                'control_category': 'AUDIT_LOGGING',
                'weight': 1.0,
                'automated_check': True,
                'check_function_name': 'check_audit_logging',
            },
            {
                'control_code': 'ISO27001-A.12.6',
                'title': 'Password & Vulnerability Management',
                'description': 'Establish a password policy and identify, evaluate, and mitigate technical vulnerabilities.',
                'control_category': 'PASSWORD_POLICY',
                'weight': 0.9,
                'automated_check': True,
                'check_function_name': 'check_password_policy',
            },
            {
                'control_code': 'ISO27001-A.16.1',
                'title': 'Incident Management',
                'description': 'Establish responsibilities and procedures to ensure a quick, effective, and orderly response to security incidents.',
                'control_category': 'INCIDENT_RESPONSE',
                'weight': 0.95,
                'automated_check': True,
                'check_function_name': 'check_incident_response',
            },
            {
                'control_code': 'ISO27001-A.17.1',
                'title': 'Information Security Continuity & Backup',
                'description': 'Plan for information security continuity as an integral part of the organisation\'s business continuity management systems.',
                'control_category': 'DATA_BACKUP',
                'weight': 0.85,
                'automated_check': True,
                'check_function_name': 'check_data_backup_policy',
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with HIPAA, NDPR, and ISO 27001 compliance frameworks and controls.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing ComplianceControl and ComplianceCheckResult data before seeding.',
        )
        parser.add_argument(
            '--no-check',
            action='store_true',
            help='Skip the initial automated compliance check run.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            from compliance.models import ComplianceCheckResult, ComplianceReport
            deleted_r = ComplianceCheckResult.objects.all().delete()[0]
            deleted_c = ComplianceControl.objects.all().delete()[0]
            deleted_p = ComplianceReport.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(
                f'Cleared {deleted_c} controls, {deleted_r} results, {deleted_p} reports.'
            ))

        # Load frameworks and controls
        for fw_data in FRAMEWORKS:
            controls_data = fw_data.pop('controls')

            fw, created = ComplianceFramework.objects.update_or_create(
                short_name=fw_data['short_name'],
                defaults={**fw_data, 'is_active': True},
            )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'{verb} framework: {fw.short_name}')

            ctrl_count = 0
            for ctrl_data in controls_data:
                _, ctrl_created = ComplianceControl.objects.get_or_create(
                    framework=fw,
                    control_code=ctrl_data['control_code'],
                    defaults=ctrl_data,
                )
                if ctrl_created:
                    ctrl_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'  OK: {ctrl_count} new controls added to {fw.short_name} '
                f'(total: {fw.engine_controls.count()})'
            ))

        # Run initial automated checks
        if not options['no_check']:
            self.stdout.write('\nRunning initial automated compliance checks…')
            checker = ComplianceChecker()
            results = checker.run_all_automated_checks()
            self.stdout.write(self.style.SUCCESS(
                f'  OK: Checks complete -- overall score: {results["overall_score"]:.1f}%  '
                f'({results["passed"]} pass / {results["failed"]} fail / '
                f'{results["partial"]} partial / {results["pending"]} pending)'
            ))

        self.stdout.write(self.style.SUCCESS(
            'Seed complete. Navigate to /compliance/ to explore the module.'
        ))
