"""Compatibility patch for undetected_chromedriver on Python 3.12+"""
import sys

def patch_distutils():
    """Patch distutils.version for Python 3.12+ compatibility."""
    if sys.version_info >= (3, 12):
        # Create fake distutils module structure
        import types
        
        # Create distutils module
        distutils = types.ModuleType('distutils')
        sys.modules['distutils'] = distutils
        
        # Create distutils.version module
        version = types.ModuleType('distutils.version')
        sys.modules['distutils.version'] = version
        distutils.version = version
        
        # Create LooseVersion class
        class LooseVersion:
            def __init__(self, vstring=None):
                if vstring:
                    self.vstring = str(vstring)
                else:
                    self.vstring = ''
                self.version = self._parse(self.vstring)
            
            def _parse(self, vstring):
                """Simple version parsing."""
                parts = []
                for part in vstring.split('.'):
                    try:
                        parts.append(int(part))
                    except ValueError:
                        parts.append(part)
                return parts
            
            def __str__(self):
                return self.vstring
            
            def __repr__(self):
                return f"LooseVersion('{self.vstring}')"
            
            def __eq__(self, other):
                return self._cmp(other) == 0
            
            def __lt__(self, other):
                return self._cmp(other) < 0
            
            def __le__(self, other):
                return self._cmp(other) <= 0
            
            def __gt__(self, other):
                return self._cmp(other) > 0
            
            def __ge__(self, other):
                return self._cmp(other) >= 0
            
            def _cmp(self, other):
                if isinstance(other, str):
                    other = LooseVersion(other)
                
                for i in range(max(len(self.version), len(other.version))):
                    v1 = self.version[i] if i < len(self.version) else 0
                    v2 = other.version[i] if i < len(other.version) else 0
                    
                    if v1 < v2:
                        return -1
                    elif v1 > v2:
                        return 1
                
                return 0
        
        # Add LooseVersion to distutils.version
        version.LooseVersion = LooseVersion

# Apply patch on import
patch_distutils()