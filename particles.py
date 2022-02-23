import numpy as np
from parcels import JITParticle, Variable

class LitterParticle(JITParticle):
    # beached : 0 sea, 1 after RK, 2 after diffusion, 3 please unbeach, 4 final beached
    beached = Variable('beached', dtype=np.int32, initial=0.)
    beached_count = Variable('beached_count', dtype=np.int32, initial=0.)
    weight = Variable('weight', dtype=np.float32, initial=0.) # [tons?]
    
    # include the traveled distance in the last x days or the time it's been beached (no ocean velocity)
    