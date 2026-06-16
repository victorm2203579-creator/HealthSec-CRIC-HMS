"""
accounts/geoip_service.py
========================
GeoIP location lookup service for login tracking.

Uses MaxMind GeoLite2-City database to determine user location
from IP address. Helps detect suspicious logins from unexpected locations.
"""

import logging
from django.conf import settings
from django.core.cache import cache

try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeoIPService:
    """Service for IP-to-location lookups using MaxMind GeoLite2."""

    def __init__(self):
        """Initialize GeoIP reader if database available."""
        self.reader = None
        self.db_path = getattr(settings, 'GEOIP2_DB_PATH', 'media/GeoLite2-City.mmdb')

        if GEOIP_AVAILABLE:
            try:
                self.reader = geoip2.database.Reader(self.db_path)
                logger.info("GeoIP2 reader initialized successfully")
            except FileNotFoundError:
                logger.warning(f"GeoLite2 database not found at {self.db_path}")
                logger.info("Download from: https://dev.maxmind.com/geoip/geoip2/geolite2/")
            except Exception as e:
                logger.error(f"Error initializing GeoIP2 reader: {e}")

    def get_location(self, ip_address):
        """
        Lookup geographic location for an IP address.

        Args:
            ip_address (str): IPv4 or IPv6 address

        Returns:
            dict: Location data with keys:
                - city: City name
                - region: State/province code
                - country: Country code (ISO 3166-1)
                - country_name: Full country name
                - latitude: Latitude coordinate
                - longitude: Longitude coordinate
                - timezone: IANA timezone
                - isp: ISP name (if available)

            Returns None if lookup fails or GeoIP not available.
        """
        if not ip_address or not self.reader:
            return None

        # Check cache first (24 hour TTL)
        cache_key = f"geoip:{ip_address}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self.reader.city(ip_address)

            location = {
                'ip_address': ip_address,
                'city': response.city.name or 'Unknown',
                'region': response.subdivisions[0].iso_code if response.subdivisions else None,
                'country': response.country.iso_code,
                'country_name': response.country.name,
                'latitude': response.location.latitude,
                'longitude': response.location.longitude,
                'timezone': response.location.time_zone,
                'isp': getattr(response, 'traits', {}).get('isp', 'Unknown'),
                'accuracy_radius': response.location.accuracy_radius,
            }

            # Cache for 24 hours
            cache.set(cache_key, location, 86400)

            return location

        except geoip2.errors.GeoIP2Error as e:
            logger.warning(f"GeoIP2 lookup failed for {ip_address}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GeoIP lookup: {e}")
            return None

    def is_suspicious_location(self, user, ip_address):
        """
        Determine if a login from this IP location is suspicious.

        Flags as suspicious if:
        1. User has never logged in from this country before
        2. IP is from a high-risk country/region
        3. Multiple logins from different countries in short time

        Args:
            user: User model instance
            ip_address: IP address to check

        Returns:
            dict: {
                'is_suspicious': bool,
                'reason': str,
                'risk_score': 0-100
            }
        """
        location = self.get_location(ip_address)
        if not location:
            return {
                'is_suspicious': False,
                'reason': 'No location data available',
                'risk_score': 0,
            }

        from audit.models import AuditLog

        # Get user's previous login locations
        previous_logins = AuditLog.objects.filter(
            user=user,
            action_category=AuditLog.ActionCategory.AUTH,
            status=AuditLog.Status.SUCCESS,
        ).values('ip_address').distinct()

        previous_countries = set()
        for log in previous_logins:
            if log['ip_address']:
                prev_location = self.get_location(log['ip_address'])
                if prev_location:
                    previous_countries.add(prev_location['country_name'])

        risk_score = 0
        reasons = []

        # Check if new country
        if location['country_name'] not in previous_countries and previous_countries:
            risk_score += 30
            reasons.append(f"New country: {location['country_name']}")

        # Check high-risk countries
        HIGH_RISK_COUNTRIES = ['North Korea', 'Iran', 'Syria', 'Cuba']
        if location['country_name'] in HIGH_RISK_COUNTRIES:
            risk_score += 50
            reasons.append(f"High-risk country: {location['country_name']}")

        # Check for VPN/proxy
        if location['isp'] and any(vpn_indicator in location['isp'].lower()
                                   for vpn_indicator in ['vpn', 'proxy', 'hosting']):
            risk_score += 20
            reasons.append(f"VPN/Proxy detected: {location['isp']}")

        return {
            'is_suspicious': risk_score >= 30,
            'reason': '; '.join(reasons) if reasons else 'Normal login pattern',
            'risk_score': min(risk_score, 100),
            'location': location,
        }

    def format_location(self, location):
        """
        Format location data for display.

        Args:
            location (dict): Location data from get_location()

        Returns:
            str: Human-readable location string
        """
        if not location:
            return 'Unknown Location'

        city = location.get('city', 'Unknown')
        country = location.get('country_name', 'Unknown')
        region = location.get('region')

        if region:
            return f"{city}, {region}, {country}"
        return f"{city}, {country}"


# Global service instance
geoip_service = GeoIPService()


def get_geoip_service():
    """Get global GeoIP service instance."""
    return geoip_service
