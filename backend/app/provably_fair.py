"""
Provably Fair Dice Logic
HMAC-SHA512 based dice roll system with seed management
"""
import hmac
import hashlib
import secrets
import os
from typing import Tuple, Dict, Any
from .config import config


class ProvablyFair:
    """Provably fair dice roll implementation"""
    
    @staticmethod
    def generate_server_seed(length: int = 64) -> str:
        """
        Generate a cryptographically secure random server seed
        
        Args:
            length: Length of the seed in characters
            
        Returns:
            Hex-encoded random seed
        """
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def generate_client_seed(user_address: str = None) -> str:
        """
        Generate client seed
        Can be user-provided or derived from user address
        
        Args:
            user_address: Optional user address to use as seed
            
        Returns:
            Client seed string
        """
        if user_address:
            return user_address
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_seed(seed: str) -> str:
        """
        Create SHA256 hash of server seed for public display
        
        Args:
            seed: Server seed to hash
            
        Returns:
            Hex-encoded SHA256 hash
        """
        return hashlib.sha256(seed.encode()).hexdigest()
    
    @staticmethod
    def calculate_roll(server_seed: str, client_seed: str, nonce: int) -> float:
        """
        Calculate provably fair dice roll using HMAC-SHA512
        
        Formula:
        1. Combine: server_seed + ":" + client_seed + ":" + nonce
        2. HMAC-SHA512 with server_seed as key
        3. Convert first 8 hex chars to integer
        4. Modulo 10000 and divide by 100 to get 0.00-99.99
        
        Args:
            server_seed: Hidden server seed
            client_seed: Public client seed
            nonce: Bet counter
            
        Returns:
            Roll result between 0.00 and 99.99
        """
        # Create message
        message = f"{client_seed}:{nonce}"
        
        # Calculate HMAC-SHA512
        hmac_result = hmac.new(
            server_seed.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        # Take first 8 characters (32 bits)
        hex_string = hmac_result[:8]
        
        # Convert to integer
        result_int = int(hex_string, 16)
        
        # Modulo 10000 to get 0-9999, then divide by 100 for 0.00-99.99
        roll = (result_int % 10000) / 100.0
        
        return round(roll, 2)
    
    @staticmethod
    def verify_roll(server_seed: str, client_seed: str, nonce: int, claimed_roll: float) -> bool:
        """
        Verify that a claimed roll is correct
        
        Args:
            server_seed: Server seed
            client_seed: Client seed
            nonce: Nonce used
            claimed_roll: The roll result to verify
            
        Returns:
            True if roll is valid
        """
        actual_roll = ProvablyFair.calculate_roll(server_seed, client_seed, nonce)
        return abs(actual_roll - claimed_roll) < 0.01  # Allow tiny floating point errors
    
    @staticmethod
    def calculate_win_chance(multiplier: float) -> float:
        """
        Calculate win chance percentage from multiplier
        
        Formula with house edge:
        win_chance = (100 - house_edge) / multiplier
        
        Args:
            multiplier: Payout multiplier (e.g., 2.0 for 2x)
            
        Returns:
            Win chance as percentage (0-100)
        """
        house_edge_percent = config.HOUSE_EDGE * 100
        win_chance = (100 - house_edge_percent) / multiplier
        return round(win_chance, 2)
    
    @staticmethod
    def calculate_multiplier(win_chance: float) -> float:
        """
        Calculate multiplier from win chance percentage
        
        Args:
            win_chance: Win chance as percentage (0-100)
            
        Returns:
            Payout multiplier
        """
        if win_chance <= 0 or win_chance >= 100:
            raise ValueError("Win chance must be between 0 and 100")
        
        house_edge_percent = config.HOUSE_EDGE * 100
        multiplier = (100 - house_edge_percent) / win_chance
        return round(multiplier, 2)
    
    @staticmethod
    def is_winning_roll(roll: float, win_chance: float) -> bool:
        """
        Determine if a roll is a winner
        
        Roll wins if: roll < win_chance
        Example: 50% win chance, rolls 0.00-49.99 win, 50.00-99.99 lose
        
        Args:
            roll: Dice roll result (0.00-99.99)
            win_chance: Win chance percentage
            
        Returns:
            True if winning roll
        """
        return roll < win_chance
    
    @staticmethod
    def calculate_payout(bet_amount: int, multiplier: float, is_win: bool) -> int:
        """
        Calculate payout amount
        
        Args:
            bet_amount: Bet amount in satoshis
            multiplier: Payout multiplier
            is_win: Whether the bet won
            
        Returns:
            Payout amount in satoshis (0 if loss)
        """
        if not is_win:
            return 0
        
        payout = int(bet_amount * multiplier)
        return payout
    
    @staticmethod
    def validate_bet_params(bet_amount: int, multiplier: float) -> Tuple[bool, str]:
        """
        Validate bet parameters
        
        Args:
            bet_amount: Bet amount in satoshis
            multiplier: Desired multiplier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check bet amount
        if bet_amount < config.MIN_BET_SATOSHIS:
            return False, f"Bet amount must be at least {config.MIN_BET_SATOSHIS} satoshis"
        
        if bet_amount > config.MAX_BET_SATOSHIS:
            return False, f"Bet amount must be at most {config.MAX_BET_SATOSHIS} satoshis"
        
        # Check multiplier
        if multiplier < config.MIN_MULTIPLIER:
            return False, f"Multiplier must be at least {config.MIN_MULTIPLIER}x"
        
        if multiplier > config.MAX_MULTIPLIER:
            return False, f"Multiplier must be at most {config.MAX_MULTIPLIER}x"
        
        # Calculate and validate win chance
        win_chance = ProvablyFair.calculate_win_chance(multiplier)
        if win_chance < 1.0 or win_chance > 98.0:
            return False, f"Win chance ({win_chance}%) is out of valid range (1-98%)"
        
        return True, ""
    
    @staticmethod
    def create_bet_result(
        server_seed: str,
        client_seed: str,
        nonce: int,
        bet_amount: int,
        multiplier: float
    ) -> Dict[str, Any]:
        """
        Complete bet processing: roll dice and calculate result
        
        Args:
            server_seed: Server seed
            client_seed: Client seed
            nonce: Nonce
            bet_amount: Bet amount in satoshis
            multiplier: Payout multiplier
            
        Returns:
            Dictionary with complete bet result
        """
        # Calculate win chance
        win_chance = ProvablyFair.calculate_win_chance(multiplier)
        
        # Roll the dice
        roll = ProvablyFair.calculate_roll(server_seed, client_seed, nonce)
        
        # Determine win/loss
        is_win = ProvablyFair.is_winning_roll(roll, win_chance)
        
        # Calculate payout
        payout = ProvablyFair.calculate_payout(bet_amount, multiplier, is_win)
        
        # Calculate profit
        profit = payout - bet_amount if is_win else -bet_amount
        
        return {
            "roll": roll,
            "win_chance": win_chance,
            "is_win": is_win,
            "payout": payout,
            "profit": profit,
            "nonce": nonce,
            "multiplier": multiplier,
            "bet_amount": bet_amount
        }
    
    @staticmethod
    def generate_verification_data(
        server_seed: str,
        server_seed_hash: str,
        client_seed: str,
        nonce: int,
        roll: float
    ) -> Dict[str, Any]:
        """
        Generate verification data for transparency
        
        Args:
            server_seed: Revealed server seed
            server_seed_hash: Original hash shown to user
            client_seed: Client seed
            nonce: Nonce used
            roll: Roll result
            
        Returns:
            Verification data dictionary
        """
        # Verify hash
        calculated_hash = ProvablyFair.hash_seed(server_seed)
        hash_valid = calculated_hash == server_seed_hash
        
        # Recalculate roll
        recalculated_roll = ProvablyFair.calculate_roll(server_seed, client_seed, nonce)
        roll_valid = abs(recalculated_roll - roll) < 0.01
        
        # Generate HMAC for verification
        message = f"{client_seed}:{nonce}"
        hmac_result = hmac.new(
            server_seed.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return {
            "server_seed": server_seed,
            "server_seed_hash": server_seed_hash,
            "server_seed_hash_valid": hash_valid,
            "client_seed": client_seed,
            "nonce": nonce,
            "hmac_sha512": hmac_result,
            "hmac_first_8_chars": hmac_result[:8],
            "hmac_decimal": int(hmac_result[:8], 16),
            "roll_calculation": f"({int(hmac_result[:8], 16)} % 10000) / 100",
            "recalculated_roll": recalculated_roll,
            "claimed_roll": roll,
            "roll_valid": roll_valid,
            "overall_valid": hash_valid and roll_valid
        }


# Convenience functions for direct use
def generate_new_seed_pair(user_address: str = None) -> Tuple[str, str, str]:
    """
    Generate new server and client seed pair
    
    Args:
        user_address: Optional user address for client seed
        
    Returns:
        Tuple of (server_seed, server_seed_hash, client_seed)
    """
    server_seed = ProvablyFair.generate_server_seed()
    server_seed_hash = ProvablyFair.hash_seed(server_seed)
    client_seed = ProvablyFair.generate_client_seed(user_address)
    
    return server_seed, server_seed_hash, client_seed


def roll_dice(server_seed: str, client_seed: str, nonce: int, bet_amount: int, multiplier: float) -> Dict[str, Any]:
    """
    Convenient wrapper for rolling dice
    
    Args:
        server_seed: Server seed
        client_seed: Client seed
        nonce: Nonce
        bet_amount: Bet amount in satoshis
        multiplier: Payout multiplier
        
    Returns:
        Complete bet result dictionary
    """
    # Validate parameters
    is_valid, error = ProvablyFair.validate_bet_params(bet_amount, multiplier)
    if not is_valid:
        raise ValueError(error)
    
    return ProvablyFair.create_bet_result(server_seed, client_seed, nonce, bet_amount, multiplier)


# Example usage and testing
if __name__ == "__main__":
    print("[DICE] Provably Fair Dice - Testing\n")
    
    # Generate seeds
    server_seed, server_seed_hash, client_seed = generate_new_seed_pair()
    
    print(f"Server Seed Hash (shown to player): {server_seed_hash}")
    print(f"Client Seed: {client_seed}")
    print(f"\nServer Seed (hidden): {server_seed}\n")
    
    # Example bet
    bet_amount = 10000  # 0.0001 BTC
    multiplier = 2.0
    nonce = 0
    
    result = roll_dice(server_seed, client_seed, nonce, bet_amount, multiplier)
    
    print(f"Bet Amount: {bet_amount} satoshis")
    print(f"Multiplier: {multiplier}x")
    print(f"Win Chance: {result['win_chance']}%")
    print(f"Nonce: {result['nonce']}")
    print(f"\nRoll Result: {result['roll']}")
    print(f"Result: {'WIN! 🎉' if result['is_win'] else 'LOSE 😢'}")
    print(f"Payout: {result['payout']} satoshis")
    print(f"Profit: {result['profit']:+d} satoshis")
    
    # Verification
    print(f"\n{'='*60}")
    print("Verification Data:")
    print(f"{'='*60}")
    
    verification = ProvablyFair.generate_verification_data(
        server_seed,
        server_seed_hash,
        client_seed,
        nonce,
        result['roll']
    )
    
    for key, value in verification.items():
        print(f"{key}: {value}")
