"""
Notifier - Sends Teams webhook notifications.

GDPR: Only sends metadata (feed name, score, event_id, link). Never sends raw content.
"""
import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Notifier:
    """
    Sends Teams webhook notifications for RSS events.
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize notifier.
        
        Args:
            webhook_url: Teams webhook URL (from env if not provided)
        """
        self.webhook_url = webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
    
    def send_teams(
        self,
        event_id: str,
        feed_id: str,
        feed_name: str,
        score: int,
        link: Optional[str] = None
    ) -> bool:
        """
        Send Teams notification for an event.
        
        Args:
            event_id: Event ID
            feed_id: Feed ID
            feed_name: Feed name
            score: Score (1-10)
            link: Optional link to article
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.warning("Teams webhook URL not configured (TEAMS_WEBHOOK_URL)")
            return False
        
        try:
            # Format Teams MessageCard payload
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": "New RSS Event",
                "themeColor": "0078D4",
                "sections": [
                    {
                        "activityTitle": f"New RSS Event from {feed_name}",
                        "activitySubtitle": f"Score: {score}/10",
                        "facts": [
                            {
                                "name": "Source",
                                "value": feed_name
                            },
                            {
                                "name": "Score",
                                "value": str(score)
                            },
                            {
                                "name": "Event ID",
                                "value": event_id[:8] + "..."
                            }
                        ]
                    }
                ]
            }
            
            # Add link action if available
            if link:
                payload["potentialAction"] = [
                    {
                        "@type": "OpenUri",
                        "name": "View Article",
                        "targets": [
                            {
                                "os": "default",
                                "uri": link
                            }
                        ]
                    }
                ]
            
            # Send webhook
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"Sent Teams notification for event {event_id}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Teams webhook HTTP error: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error sending Teams notification: {e}")
            return False


# Global instance
notifier = Notifier()

