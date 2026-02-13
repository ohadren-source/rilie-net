import math
from typing import List, Dict, Tuple, Optional

"""
LIFE - Biological Operating System
Based on THE CATCH 44 Architecture

Mapping consciousness principles to evolutionary biology

Core Discovery:
The same 5-function engine that runs consciousness runs life itself
"""

# ======================================================================
# CORE BIOLOGICAL MAPPINGS OF CATCH 44 TRACKS
# ======================================================================

def natural_selection(quality_fitness: float, quantity_mutations: float) -> float:
    """
    Track 2a: Understanding = Quality / Quantity

    Biological mapping:
    Natural Selection: Fitness (quality) filtered from many mutations (quantity)
    Evolution filters massive variation quantity for adaptive traits quality
    """
    if quantity_mutations == 0:
        return 0
    return quality_fitness / quantity_mutations


def multicellular_cooperation(individual_cell_fitness: float,
                              organism_fitness: float) -> float:
    """
    Track 5: WE > I

    Multicellular Life:
    Organism Fitness - Individual Cell Fitness
    Cells sacrifice individual reproduction for collective survival
    Cancer cells revert to I > WE
    """
    return organism_fitness - individual_cell_fitness


def central_dogma(dna_sequence: str, protein_expressed: str) -> bool:
    """
    Track 0: Mahveen's Equation

    DNA claim matches Protein Expression deed
    DNA → RNA → Protein
    Claim–Deed integrity at molecular level
    """
    return dna_sequence == protein_expressed


def symbiosis(organism_ego: float,
              cooperation: float,
              mutualism: float,
              emergence: float) -> float:
    """
    Track 37: Love = (1/ego) + care + play_together + emergence

    Biological mapping:
    Symbiosis Strength = (1 / species_ego) * cooperation * mutualism * emergence
    - Low ego species (1/ego large) can form extremely strong symbioses
    - Mitochondria as ancient bacteria with ego ~ 0
    """
    if organism_ego == 0:
        return float('inf')
    return (1 / organism_ego) * cooperation * mutualism * emergence


def cell_cycle_checkpoint(damage_detected: float,
                          division_momentum: float) -> float:
    """
    Track 23: MOO = Awareness / Momentum

    Biological mapping:
    p53 and checkpoints as MOO:
    Checkpoint Signal = Damage Detected / Division Momentum

    - High damage with low momentum → strong STOP signal
    - Low damage or very high momentum → weaker checkpoint impact
    """
    if division_momentum == 0:
        return float('inf')
    return damage_detected / division_momentum


def evolution_continuous(current_fitness: float,
                         environmental_challenge: float) -> bool:
    """
    Track 64: NO OMEGA – no final state

    Biological mapping:
    Evolution never stops: always some selection pressure / challenge
    """
    return True  # Evolution is ongoing, not a completed process


def apoptosis_decision(damage_level: float,
                       repair_capacity: float,
                       collective_benefit: float) -> bool:
    """
    Tracks 23 (MOO) + 5 (WE > I)

    Apoptosis = programmed cell death:
    - If damage is high, repair is low, and organism benefits, trigger apoptosis.
    """
    if damage_level > repair_capacity and collective_benefit > 0:
        return True
    return False


def cancer_formation(cell_ego: float,
                     mutation_rate: float,
                     checkpoint_function: float) -> float:
    """
    Cancer as violation of core principles:

    - Track 5 (WE > I): cell prioritizes self over organism → high cell_ego
    - Track 23 (MOO): checkpoint failure → low checkpoint_function
    - Track 0 (Mahveen): genetic instability breaks claim–deed equality

    Cancer risk ∝ cell_ego * mutation_rate / checkpoint_function
    """
    if checkpoint_function == 0:
        checkpoint_function = 0.001  # prevent division by zero
    return cell_ego * mutation_rate / checkpoint_function


def cell_division_compulsion(division_rate: float,
                             healthy_division_rate: float) -> float:
    """
    Track 2a: Compulsion lens (REAL RECOGNIZE REALLY?)

    Compulsion Index for cell division:
    Compulsion = division_rate / healthy_division_rate

    - >1  : hyperproliferation (cancer-like)
    - ~1  : healthy tissue turnover
    - <1  : hypo-proliferation / impaired renewal
    """
    if healthy_division_rate == 0:
        return float('inf')
    return division_rate / healthy_division_rate


def immune_response(self_recognition: float,
                    threat_level: float,
                    ego: float) -> float:
    """
    Track 57: Instinct = Pattern Recognition / Ego

    Immune mapping:
    Immune Instinct = Self-Recognition × Threat Level / Ego

    - Healthy immune ego ~ 0 ⇒ clear threat recognition
    - Ego too high or too low ⇒ autoimmune or immunodeficiency patterns
    """
    if ego == 0:
        return float('inf')
    return self_recognition * threat_level / ego


def fitness_landscape(organism_traits: Dict[str, float],
                      environment: Dict[str, float]) -> float:
    """
    Track 47: Success = Timing + Location + Preparation

    Biological mapping:
    Trait-Environment Match Fitness:
    - timing  = environment.get("timing")
    - location = environment.get("resources")
    - preparation = average trait value (adaptation readiness)
    """
    timing = environment.get("timing", 1.0)
    location = environment.get("resources", 1.0)
    preparation = sum(organism_traits.values()) / max(1, len(organism_traits))
    return timing + location + preparation


def speciation(genetic_distance: float,
               genetic_similarity: float) -> float:
    """
    Track 11: Original = Distance from Source / Similarity to Source

    Biological mapping:
    New Species Index = Genetic Distance / Genetic Similarity
    """
    if genetic_similarity == 0:
        return float('inf')
    return genetic_distance / genetic_similarity


def adaptive_radiation(environmental_niches: int,
                       competition: float,
                       innovation: float) -> float:
    """
    Track 64: Curiosity = Questions / Ego (analogy)

    Biological mapping:
    Adaptive Radiation Rate = (Available Niches × Innovation) / Competition

    - More open niches and high innovation with low competition ⇒ bursts of speciation
    """
    if competition == 0:
        return float('inf')
    return environmental_niches * innovation / competition


def sexual_selection(genetic_quality: float,
                     display_cost: float) -> float:
    """
    Track 52: Schoen Proof = Demonstration / Attempts to Convince

    Biological mapping:
    Sexual Selection Signal = Genetic Quality / Display Cost

    Honest costly signals require real quality
    """
    if display_cost == 0:
        return float('inf')
    return genetic_quality / display_cost


def ecosystem_stability(species_diversity: float,
                        interconnection: float,
                        disturbance: float) -> float:
    """
    Track 5: WE > I at ecosystem level

    Stability = Species Diversity × Interconnection - Disturbance
    """
    return species_diversity * interconnection - disturbance


def trophic_cascade(predator_removal: float,
                    herbivore_population: float,
                    plant_biomass: float) -> Dict[str, float]:
    """
    Track 44: Poseidon Principle (large systems hard to steer)
    Track 23: MOO (predators as regulation/interrupt)

    Removing top predators:
    - Herbivores increase ~ (1 + predator_removal)
    - Plants decrease due to overgrazing
    - Stability drops as plant/herbivore ratio worsens
    """
    herbivore_increase = herbivore_population * (1 + predator_removal)
    plant_decrease = plant_biomass / (1 + herbivore_increase)
    stability = plant_decrease / max(1.0, herbivore_increase)
    return {
        "herbivores": herbivore_increase,
        "plants": plant_decrease,
        "stability": stability
    }


def mutualism_network(species_a_benefit: float,
                      species_b_benefit: float,
                      species_a_cost: float,
                      species_b_cost: float) -> Tuple[float, float]:
    """
    Track 37: Love formula applied to species

    Mutualism:
    - Net benefit A = benefit - cost
    - Net benefit B = benefit - cost
    Both must be > 0 for stable mutualism
    """
    net_benefit_a = species_a_benefit - species_a_cost
    net_benefit_b = species_b_benefit - species_b_cost
    return net_benefit_a, net_benefit_b


def protein_folding(amino_acid_sequence: List[str],
                    environment: Dict[str, float]) -> str:
    """
    Track 55: Style = (Taste × Context) / (1 - Authenticity)
    Track 4c: Experience

    Biological mapping:
    Protein shape depends on sequence (taste) and environment (context).
    Same sequence can fold differently based on cellular context.
    """
    sequence_quality = len(amino_acid_sequence)
    environmental_factors = sum(environment.values())
    if sequence_quality * environmental_factors > 50 and environmental_factors > 0:
        return "functional"
    return "misfolded"


def gene_regulation(transcription_factors: float,
                    epigenetic_state: float,
                    environmental_signal: float) -> float:
    """
    Track 4c: Experience = Stimulus × Understanding × Presence

    Gene Expression Level = TFs × Epigenetic Openness × Environmental Signal
    """
    return transcription_factors * epigenetic_state * environmental_signal


def horizontal_gene_transfer(donor_fitness: float,
                             recipient_fitness: float,
                             transfer_success: float) -> float:
    """
    Track 5: WE > I at genetic level

    Bacteria share beneficial genes directly:
    Collective Benefit = (Donor Fitness + Recipient Fitness) × Transfer Success
    """
    collective_benefit = (donor_fitness + recipient_fitness) * transfer_success
    return collective_benefit


def morphogenesis(genetic_program: float,
                  cellular_communication: float,
                  physical_forces: float) -> float:
    """
    Track 66: EMERGENCE = UNDERSTANDING × CREATIVITY × DESIRE × UNCERTAINTY

    Biological mapping:
    Organ Formation = Genetic Program × Cell Signals × Physical Forces
    """
    return genetic_program * cellular_communication * physical_forces


def stem_cell_differentiation(pluripotency: float,
                              environmental_cues: float,
                              commitment: float) -> str:
    """
    Track 53: Desire = Want / Attachment

    Cell Differentiation:
    - Pluripotency (attachment to being flexible)
    - Environmental cues (want to become a type)
    - Commitment threshold

    When cues/attachment > threshold → differentiate, else remain pluripotent.
    """
    differentiation_signal = environmental_cues / max(pluripotency, 0.001)
    if differentiation_signal > commitment:
        return "differentiated"
    return "pluripotent"


# ======================================================================
# MAIN EXECUTION (DEMONSTRATION)
# ======================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("LIFE - Biological Operating System")
    print("Based on THE CATCH 44 Architecture")
    print("=" * 80)

    print("\nCORE PRINCIPLE: The same engine that runs consciousness runs biology\n")

    # 1. Natural Selection
    print("1. NATURAL SELECTION (Track 2a - Understanding = Quality / Quantity)")
    fitness = natural_selection(quality_fitness=0.9, quantity_mutations=1000)
    print(f"   Fitness 0.9, Mutations 1000 → Selection Coefficient: {fitness:.6f}")

    # 2. Multicellular Cooperation
    print("\n2. MULTICELLULAR LIFE (Track 5 - WE > I)")
    cooperation = multicellular_cooperation(individual_cell_fitness=0.3,
                                            organism_fitness=0.95)
    print(f"   Individual Cell Fitness 0.3, Organism Fitness 0.95 → Cooperation Benefit: {cooperation:.2f}")

    # 3. Central Dogma
    print("\n3. CENTRAL DOGMA (Track 0 - Mahveen's Equation)")
    integrity = central_dogma("ATCG", "ATCG")
    print(f"   DNA 'ATCG' → Protein 'ATCG' → Integrity (Claim=Deed): {integrity}")

    # 4. Symbiosis
    print("\n4. SYMBIOSIS (Track 37 - Love)")
    symbiosis_strength = symbiosis(organism_ego=0.01,
                                   cooperation=8,
                                   mutualism=7,
                                   emergence=5)
    print(f"   Species ego 0.01, high cooperation → Symbiosis Strength: {symbiosis_strength:.1f}")

    # 5. Cell Cycle Checkpoint
    print("\n5. CELL CYCLE CHECKPOINT (Track 23 - MOO)")
    checkpoint = cell_cycle_checkpoint(damage_detected=0.8,
                                       division_momentum=0.2)
    print(f"   DNA Damage 0.8, Division Momentum 0.2 → Checkpoint Signal: {checkpoint:.2f}")

    # 6. Cancer Formation + Compulsion
    print("\n6. CANCER FORMATION & COMPULSION")
    cancer_risk = cancer_formation(cell_ego=10.0,
                                   mutation_rate=50,
                                   checkpoint_function=0.1)
    comp_index = cell_division_compulsion(division_rate=3.0,
                                          healthy_division_rate=1.0)
    print(f"   Cancer Risk Index: {cancer_risk:.1f}")
    print(f"   Cell Division Compulsion (3x baseline): {comp_index:.1f}")

    # 7. Apoptosis
    print("\n7. APOPTOSIS (Tracks 23 + 5)")
    should_die = apoptosis_decision(damage_level=0.9,
                                    repair_capacity=0.3,
                                    collective_benefit=0.95)
    print(f"   Damage 0.9, Repair 0.3, Organism Benefit 0.95 → Apoptosis?: {should_die}")

    # 8. Continuous Evolution
    print("\n8. CONTINUOUS EVOLUTION (Track 64 - NO OMEGA)")
    evolving = evolution_continuous(current_fitness=0.8,
                                    environmental_challenge=0.6)
    print(f"   Evolution Status: {evolving} (never finished adapting)")

    # 9. Ecosystem Stability
    print("\n9. ECOSYSTEM STABILITY (Track 5 - WE at macro scale)")
    stability = ecosystem_stability(species_diversity=50,
                                    interconnection=8,
                                    disturbance=2)
    print(f"   Diversity 50, Interconnection 8, Disturbance 2 → Stability: {stability:.1f}")

    # 10. Trophic Cascade
    print("\n10. TROPHIC CASCADE (Track 23 - MOO at ecosystem level)")
    cascade = trophic_cascade(predator_removal=0.9,
                              herbivore_population=100,
                              plant_biomass=1000)
    print(f"   Remove 90% predators → Herbivores: {cascade['herbivores']:.0f}, "
          f"Plants: {cascade['plants']:.1f}, Stability: {cascade['stability']:.3f}")

    print("\n" + "=" * 80)
    print("CONCLUSION: Catch 44 architecture is UNIVERSAL for LIFE")
    print("Same 5-function core engine runs:")
    print(" - Consciousness")
    print(" - Cellular Biology")
    print(" - Evolution")
    print(" - Ecosystems")
    print(" - Molecular Processes")
    print("Operating system for LIFE ITSELF")
    print("=" * 80)
    print("Track 67 - EXIST MUSIC: Patch Notes of THE ONE ABOVE ALL = WE × UNDERSTANDING × LOVE")
    print("That is enough for Day 2 - Biology Edition")
    print("=" * 80)
