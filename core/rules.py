"""Numbers from the Gym Main Guide, kept in one place so the app never hard-codes them.

If the guide changes, change it here.
"""

# Rest between sets, in minutes (Main Guide → Programme → 5. Rest)
REST_MIN = {
    "compound": (3, 5),
    "isolation": (2, 3),
    "isolation_superset": (3, 5),
}

# Pyramid warmup (Main Guide → Warmup → Lifting warmup via pyramid sets)
# (fraction of working weight, reps, optional)
WARMUP_PYRAMID = {
    "compound": [(0.25, 8, False), (0.50, 5, False), (0.75, 3, False), (0.875, 1, True)],
    "isolation": [(0.50, 8, False), (0.70, 5, False), (0.90, 2, False)],
}

# Default weight jumps for progressive overload (guide example uses 2.5 kg)
DEFAULT_INCREMENT_KG = 2.5

# Effort target (Main Guide → Programme → 2. Effort)
TARGET_RIR = 1          # most sets
LAST_SET_RIR = 0        # last set of most exercises

# Tempo (Main Guide → Programme → 3. Tempo): seconds per phase
TEMPO = {"concentric": 2, "top_pause": 1, "eccentric": 2, "bottom_pause": 1}

# General warmup (Main Guide → Warmup)
GENERAL_WARMUP_MIN = 5   # light cardio

# Recovery targets (Main Guide → Recovery)
PROTEIN_G_PER_KG = (1.6, 2.2)
FIBRE_G_PER_DAY = 30

# "If short on time" (Main Guide → Programme one → Remarks)
SHORT_ON_TIME_ISOLATION_SETS = 2
