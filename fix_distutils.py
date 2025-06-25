import sys

# Create a mock distutils.version module for compatibility
class LooseVersion:
    def __init__(self, vstring):
        self.vstring = str(vstring)
        self.version = vstring
    
    def __str__(self):
        return self.vstring
    
    def __repr__(self):
        return f"LooseVersion('{self.vstring}')"
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __lt__(self, other):
        # Simple numeric comparison for Chrome versions
        try:
            return int(str(self).split('.')[0]) < int(str(other).split('.')[0])
        except:
            return str(self) < str(other)
    
    def __le__(self, other):
        return self == other or self < other
    
    def __gt__(self, other):
        return not self <= other
    
    def __ge__(self, other):
        return not self < other

class MockDistutils:
    class version:
        LooseVersion = LooseVersion
            
distutils = MockDistutils()
sys.modules['distutils'] = distutils
sys.modules['distutils.version'] = distutils.version
