import yaml
from pathlib import Path
from typing import Optional
from ..models.circuit import CircuitProfile

class CircuitProfileLoader:
    """Responsible for loading circuit profiles from YAML files."""

    def __init__(self, profiles_dir: Optional[str] = None):
        """
        Initialize the loader.
        
        Args:
            profiles_dir: Directory where circuit profiles are stored. 
                          Defaults to 'src/digital_twin_lab/data/circuit_profiles' if not provided.
        """
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            # Try to find the data directory relative to this file
            # This file is in src/digital_twin_lab/circuit/
            # Data is in src/digital_twin_lab/data/circuit_profiles/
            self.profiles_dir = Path(__file__).parent.parent / "data" / "circuit_profiles"

    def load_profile(self, circuit_id: str) -> CircuitProfile:
        """
        Load a circuit profile by its ID.
        
        Args:
            circuit_id: The ID of the circuit to load.
            
        Returns:
            The loaded CircuitProfile.
            
        Raises:
            FileNotFoundError: If the profile file is not found.
            ValueError: If the profile data is invalid.
        """
        profile_path = self.profiles_dir / f"{circuit_id}.yaml"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Circuit profile for '{circuit_id}' not found at {profile_path}")
        
        try:
            with open(profile_path, 'r') as f:
                data = yaml.safe_load(f)
            return CircuitProfile(**data)
        except Exception as e:
            raise ValueError(f"Failed to load circuit profile '{circuit_id}': {e}")

    def list_available_profiles(self) -> list[str]:
        """
        List all available circuit profile IDs.
        
        Returns:
            A list of circuit IDs.
        """
        if not self.profiles_dir.exists():
            return []
        return [p.stem for p in self.profiles_dir.glob("*.yaml")]
