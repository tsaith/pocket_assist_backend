
from enum import Enum
from typing import Dict, Optional

from app.lib.supabase import supabase_admin


class SubscriptionFeature(Enum):
    """Subscription feature enumeration"""
    REMINDERS = "reminders"
    NOTES = "notes"
    BOOKKEEPING = "bookkeeping"


class SubscriptionLimits:
    """Subscription limits constants and utility methods"""
    
    # Define limits for each tier and feature
    LIMITS: Dict[str, Dict[str, int]] = {
        'free': {
            'reminders': 5,
            'notes': 5,
            'bookkeeping_months': 3
        },
        'pro': {
            'reminders': 30,
            'notes': 50,
            'bookkeeping_months': 12
        },
        'vip': {
            'reminders': 100,
            'notes': 200,
            'bookkeeping_months': 36
        },
        'vvip': {
            'reminders': -1,  # -1 means unlimited
            'notes': -1,      # -1 means unlimited
            'bookkeeping_months': -1  # -1 means unlimited
        }
    }
    
    @staticmethod
    def get_limit(feature: SubscriptionFeature, tier: str) -> int:
        """
        Get limit for specific feature based on subscription tier
        
        Args:
            feature: The subscription feature
            tier: The subscription tier (free, pro, vip, vvip)
            
        Returns:
            int: The limit for the feature (-1 means unlimited)
        """
        if tier not in SubscriptionLimits.LIMITS:
            tier = 'free'  # Default to free tier
        
        tier_limits = SubscriptionLimits.LIMITS[tier]
        
        if feature == SubscriptionFeature.REMINDERS:
            return tier_limits['reminders']
        elif feature == SubscriptionFeature.NOTES:
            return tier_limits['notes']
        elif feature == SubscriptionFeature.BOOKKEEPING:
            return tier_limits['bookkeeping_months']
        else:
            return 0
    
    @staticmethod
    def get_limit_message(feature: SubscriptionFeature, tier: str, current_count: int) -> str:
        """
        Get limit message for specific feature
        
        Args:
            feature: The subscription feature
            tier: The subscription tier
            current_count: Current count of the feature
            
        Returns:
            str: The limit message
        """
        limit = SubscriptionLimits.get_limit(feature, tier)
        
        # Handle unlimited case
        if limit == -1:
            return f"You have unlimited {feature.value} with {tier.upper()} subscription."
        
        tier_display = tier.upper()
        
        if feature == SubscriptionFeature.REMINDERS:
            return f"You have reached the maximum limit of {limit} reminders for {tier_display} subscription. Please consider upgrading to a higher tier."
        elif feature == SubscriptionFeature.NOTES:
            return f"You have reached the maximum limit of {limit} notes for {tier_display} subscription. Please consider upgrading to a higher tier."
        elif feature == SubscriptionFeature.BOOKKEEPING:
            return f"You have reached the maximum limit of {limit} months of bookkeeping records for {tier_display} subscription. Please consider upgrading to a higher tier."
        else:
            return f"Limit reached for {tier_display} subscription. Please consider upgrading to a higher tier."
    
    @staticmethod
    def is_limit_reached(feature: SubscriptionFeature, tier: str, current_count: int) -> bool:
        """
        Check if the limit has been reached for a specific feature
        
        Args:
            feature: The subscription feature
            tier: The subscription tier
            current_count: Current count of the feature
            
        Returns:
            bool: True if limit is reached, False otherwise
        """
        limit = SubscriptionLimits.get_limit(feature, tier)
        
        # -1 means unlimited
        if limit == -1:
            return False
        
        return current_count >= limit


def get_user_tier(user_id: str) -> str:
    """
    Get user's subscription tier from database
    
    Args:
        user_id: The user's ID
        
    Returns:
        str: The subscription tier (free, pro, vip, vvip)
    """
    try:
        # Query subscriptions table
        response = supabase_admin.from_("subscriptions").select("tier").eq("user_id", user_id).execute()
        
        if not response.data:
            # No subscription record found, return default tier
            print(f"No subscription found for user ID {user_id}, defaulting to 'free'")
            return 'free'
        
        tier = response.data[0].get("tier", "free")
        return tier
        
    except Exception as e:
        error_msg = f"Error getting subscription tier: {str(e)}"
        print(error_msg)
        # Return free tier on error
        return 'free'


class UserSubscriptionManager:
    """Manager class for user subscription operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize UserSubscriptionManager
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self.tier: Optional[str] = None
    
    def get_tier(self) -> str:
        """
        Get user's subscription tier
        
        Returns:
            str: The subscription tier (free, pro, vip, vvip)
        """
        if self.tier is None:
            self.tier = get_user_tier(self.user_id)
        return self.tier
    
    def refresh_tier(self) -> str:
        """
        Refresh and get the latest subscription tier from database
        
        Returns:
            str: The subscription tier
        """
        self.tier = get_user_tier(self.user_id)
        return self.tier
    
    def get_reminders_limit(self) -> int:
        """
        Get reminders limit for user's subscription tier
        
        Returns:
            int: The reminders limit (-1 means unlimited)
        """
        tier = self.get_tier()
        return SubscriptionLimits.get_limit(SubscriptionFeature.REMINDERS, tier)
    
    def get_notes_limit(self) -> int:
        """
        Get notes limit for user's subscription tier
        
        Returns:
            int: The notes limit (-1 means unlimited)
        """
        tier = self.get_tier()
        return SubscriptionLimits.get_limit(SubscriptionFeature.NOTES, tier)
    
    def get_bookkeeping_months_limit(self) -> int:
        """
        Get bookkeeping months limit for user's subscription tier
        
        Returns:
            int: The bookkeeping months limit (-1 means unlimited)
        """
        tier = self.get_tier()
        return SubscriptionLimits.get_limit(SubscriptionFeature.BOOKKEEPING, tier)
    
    def get_feature_limit(self, feature: SubscriptionFeature) -> int:
        """
        Get limit for any feature
        
        Args:
            feature: The subscription feature
            
        Returns:
            int: The feature limit (-1 means unlimited)
        """
        tier = self.get_tier()
        return SubscriptionLimits.get_limit(feature, tier)
    
    def is_limit_reached(self, feature: SubscriptionFeature, current_count: int) -> bool:
        """
        Check if limit is reached for a feature
        
        Args:
            feature: The subscription feature
            current_count: Current count of the feature
            
        Returns:
            bool: True if limit is reached, False otherwise
        """
        tier = self.get_tier()
        return SubscriptionLimits.is_limit_reached(feature, tier, current_count)
    
    def get_limit_message(self, feature: SubscriptionFeature, current_count: int) -> str:
        """
        Get limit message for a feature
        
        Args:
            feature: The subscription feature
            current_count: Current count of the feature
            
        Returns:
            str: The limit message
        """
        tier = self.get_tier()
        return SubscriptionLimits.get_limit_message(feature, tier, current_count)
