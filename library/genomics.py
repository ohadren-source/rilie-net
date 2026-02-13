"""
GENOMICS & GENETICS - The Information Layer
Based on THE CATCH 44 Architecture

The code layer between molecular chemistry and living biology

EXTENDED STACK:
- BIOCHEMISTRY = Molecular mechanisms
- GENOMICS = Information/Code layer  
- BIOLOGY = Functional organisms
- NEUROSCIENCE = Specialized neural substrate
- CATCH 44 = Operating System
- LINGUISTICS = Communication interface

From molecules → code → life → consciousness → language
"""

import random
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# ============================================================================
# CORE ENGINE MAPPINGS
# Catch 44 → Genomics
# ============================================================================

def genomic_information_density(coding_sequence: int,
                               total_genome: int) -> float:
    """
    Track #2a: Understanding = Quality/Quantity
    
    Information Density = Coding DNA / Total Genome
    
    Human: ~2% codes for proteins, rest is regulatory/structural
    Efficiency isn't just protein-coding - regulation matters too
    """
    if total_genome == 0:
        return 0.0
    return coding_sequence / total_genome


def gene_network_effect(individual_gene: float,
                        network_regulation: float) -> float:
    """
    Track #5: WE > I
    
    Gene Function = Network Regulation - Individual Expression
    
    No gene works alone
    Master regulators control hundreds of downstream genes
    Cancer = when I > WE (cell ignores collective signals)
    """
    return network_regulation - individual_gene


def genotype_phenotype_integrity(dna_sequence: str,
                                 protein_function: str,
                                 environment: Dict[str, float]) -> bool:
    """
    Track #0: Mahveen's Equation
    
    Genotype (claim) + Environment → Phenotype (deed)
    
    DNA sequence is the "claim" about what protein to make
    Actual function depends on cellular context
    Same gene, different environments = different outcomes
    """
    # Simplified: does sequence produce functional protein in this context?
    return len(dna_sequence) > 0 and len(protein_function) > 0


def transcription_factor_interrupt(baseline_expression: float,
                                   tf_binding: bool,
                                   tf_strength: float) -> float:
    """
    Track #23: MOO (Interruption)
    
    Transcription Factor = Gene Expression Interrupt
    
    Genes transcribing → TF binds → expression changes
    Pattern interrupt at molecular level
    """
    if tf_binding:
        return baseline_expression * tf_strength
    return baseline_expression


def phenotype_emergence(genotype: Set[str],
                       environment: Dict[str, float],
                       development_history: List[float]) -> float:
    """
    Track #67: EMERGENCE
    
    Phenotype = Genotype × Environment × Development
    
    You can't predict phenotype from DNA alone
    Epigenetics, maternal effects, stochastic events all matter
    The organism emerges from interactions, not just code
    """
    genetic_component = len(genotype)
    environmental_component = sum(environment.values())
    developmental_component = sum(development_history)
    
    return genetic_component * environmental_component * developmental_component


# ============================================================================
# CENTRAL DOGMA & INFORMATION FLOW
# ============================================================================

def central_dogma_flow(dna: str) -> Tuple[str, str]:
    """
    Track #64: NO OMEGA - but with directionality
    
    DNA → RNA → Protein (mostly)
    
    Information flows one direction (mostly)
    But reverse transcriptase exists (retroviruses)
    And epigenetics adds feedback loops
    So it's not truly "central" or "dogmatic"
    """
    rna = dna.replace('T', 'U')  # Simplified transcription
    protein = f"protein_from_{rna[:10]}"  # Simplified translation
    return rna, protein


def genetic_code_redundancy(amino_acid: str) -> int:
    """
    Track #6: Pair of Ducks - Redundancy in genetic code
    
    Multiple codons → same amino acid
    
    64 codons, only 20 amino acids
    Degeneracy provides error tolerance
    Third position often doesn't matter ("wobble")
    """
    # Simplified mapping
    redundancy_map = {
        'Leucine': 6,
        'Serine': 6,
        'Arginine': 6,
        'Glycine': 4,
        'Methionine': 1,  # Only AUG
        'Tryptophan': 1   # Only UGG
    }
    return redundancy_map.get(amino_acid, 3)  # Default ~3 per amino acid


def mutation_rate_vs_repair(errors_per_replication: float,
                            repair_efficiency: float) -> float:
    """
    Track #0: Integrity at replication level
    
    DNA Polymerase makes ~1 error per 10^7 bases
    Repair mechanisms fix most
    
    What gets through = evolution's raw material
    Too many errors = cancer/death
    Too few = no adaptation
    """
    unrepaired_errors = errors_per_replication * (1 - repair_efficiency)
    return unrepaired_errors


# ============================================================================
# GENE REGULATION & EPIGENETICS
# ============================================================================

def promoter_strength(tfbs_count: int,
                     tfbs_affinity: float,
                     chromatin_accessibility: float) -> float:
    """
    Track #2a: Quality of signal = Understanding
    
    Gene expression depends on:
    - How many transcription factor binding sites
    - How strong the binding
    - Whether chromatin allows access
    
    Signal quality determines output
    """
    return tfbs_count * tfbs_affinity * chromatin_accessibility


def epigenetic_memory(dna_methylation: float,
                     histone_modification: float,
                     generations_maintained: int) -> float:
    """
    Track #34: Memory without changing sequence
    
    Epigenetics = information layer ON TOP of DNA
    
    DNA sequence stays same
    Expression pattern changes
    Can be inherited across generations
    """
    epigenetic_state = (dna_methylation + histone_modification) / 2
    return epigenetic_state * generations_maintained


def enhancer_distance_independence(enhancer_position: int,
                                   promoter_position: int,
                                   looping_machinery: float) -> float:
    """
    Track #37: Entanglement-like action at a distance
    
    Enhancers regulate genes far away
    
    DNA loops to bring distant sequences together
    Spatial organization matters beyond linear sequence
    """
    distance = abs(enhancer_position - promoter_position)
    # Looping overcomes distance
    effective_regulation = looping_machinery / (1 + (distance * 0.0001))
    return effective_regulation


def alternative_splicing(exons: List[str],
                        splicing_factors: Dict[str, float]) -> List[str]:
    """
    Track #67: EMERGENCE - one gene, many proteins
    
    Alternative Splicing creates protein diversity
    
    ~20,000 genes → ~100,000+ proteins
    Same code, different combinations
    Context determines which exons included
    """
    # Simplified: randomly include/exclude exons based on factors
    included_exons = []
    for exon in exons:
        if random.random() < splicing_factors.get(exon, 0.5):
            included_exons.append(exon)
    return included_exons


# ============================================================================
# REGULATORY NETWORKS
# ============================================================================

def gene_regulatory_network(genes: Dict[str, float],
                           regulatory_matrix: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Track #5: WE > I at gene level
    
    Genes form networks where each regulates others
    
    Master regulators control cascades
    Feedback loops create stability or oscillation
    Network topology determines cell fate
    """
    new_expression = {}
    for gene, current_level in genes.items():
        regulators = regulatory_matrix.get(gene, [])
        if regulators:
            # Simplified: average of regulator effects
            regulation = sum(genes.get(r, 0) for r in regulators) / len(regulators)
            new_expression[gene] = (current_level + regulation) / 2
        else:
            new_expression[gene] = current_level
    return new_expression


def master_regulator_cascade(master_gene: float,
                             downstream_genes: int,
                             amplification: float) -> float:
    """
    Track #9d: Small cause, large effect (leverage)
    
    One master regulator controls hundreds of genes
    
    Hox genes determine body segment identity
    Small change in master = massive phenotypic change
    """
    return master_gene * (downstream_genes ** amplification)


def feedback_loop_stability(gene_a: float,
                           gene_b: float,
                           loop_type: str) -> Tuple[float, float]:
    """
    Track #23: MOO through feedback
    
    Negative feedback = stability (MOO prevents runaway)
    Positive feedback = switch-like behavior
    """
    if loop_type == "negative":
        # A inhibits B, B inhibits A = stable oscillation
        new_a = gene_a * (1 - gene_b * 0.1)
        new_b = gene_b * (1 - gene_a * 0.1)
    else:  # positive
        # A activates B, B activates A = bistable switch
        new_a = gene_a * (1 + gene_b * 0.1)
        new_b = gene_b * (1 + gene_a * 0.1)
    return new_a, new_b


# ============================================================================
# HORIZONTAL GENE TRANSFER & VARIATION
# ============================================================================

def horizontal_gene_transfer(organism_a_genome: Set[str],
                            organism_b_genome: Set[str],
                            transfer_rate: float) -> Set[str]:
    """
    Track #5: WE > I across species
    
    Bacteria share genes across species boundaries
    
    Antibiotic resistance spreads via plasmids
    Evolution isn't just vertical (parent to child)
    Horizontal sharing accelerates adaptation
    """
    transferred_genes = set()
    for gene in organism_b_genome:
        if random.random() < transfer_rate:
            transferred_genes.add(gene)
    return organism_a_genome.union(transferred_genes)


def genetic_drift_vs_selection(population_size: int,
                              selection_coefficient: float,
                              generations: int) -> str:
    """
    Track #8: Some things on a curve (neutral theory)
    
    Small populations: drift dominates
    Large populations: selection dominates
    Most mutations: neutral (neither help nor hurt)
    """
    drift_strength = 1 / population_size
    
    if selection_coefficient > drift_strength * 10:
        return "selection_dominant"
    elif drift_strength > selection_coefficient * 10:
        return "drift_dominant"
    else:
        return "both_matter"


def mutation_spectrum(mutagen: str) -> Dict[str, float]:
    """
    Different mutagens create different mutation patterns
    
    UV light: thymine dimers
    Oxidative stress: G→T transversions
    Replication errors: indels at repeats
    """
    spectrum = {
        "UV": {"T-T_dimer": 0.8, "other": 0.2},
        "oxidative": {"G_to_T": 0.6, "other": 0.4},
        "replication": {"indel": 0.5, "point": 0.5}
    }
    return spectrum.get(mutagen, {"point": 1.0})


# ============================================================================
# JUNK DNA & REGULATORY ELEMENTS
# ============================================================================

def non_coding_function(sequence_type: str) -> Dict[str, float]:
    """
    Track #2a: Quality over Quantity
    
    "Junk DNA" isn't junk
    
    - Enhancers regulate distant genes
    - lncRNA modulates chromatin state
    - Transposons drive evolution
    - Structural maintenance
    
    Only 2% codes proteins, but 80%+ is functional
    """
    functions = {
        "enhancer": {"regulatory": 0.9, "structural": 0.1},
        "lncRNA": {"chromatin_regulation": 0.7, "splicing": 0.3},
        "transposon": {"evolutionary_innovation": 0.5, "regulatory": 0.3, "junk": 0.2},
        "intron": {"splicing_regulation": 0.6, "structural": 0.4}
    }
    return functions.get(sequence_type, {"unknown": 1.0})


def three_d_genome_organization(linear_distance: int,
                               topological_domain: str) -> float:
    """
    Track #37: Non-local interactions
    
    Genome organized in 3D, not just linear
    
    TADs (Topologically Associating Domains)
    Genes interact based on 3D proximity, not sequence proximity
    """
    # Genes in same TAD interact more despite linear distance
    if topological_domain == "same_TAD":
        return 1.0 / (1 + linear_distance * 0.001)  # Weak distance effect
    else:
        return 1.0 / (1 + linear_distance * 0.1)    # Strong distance effect


# ============================================================================
# GENOMIC CONFLICT & PARASITES
# ============================================================================

def selfish_genetic_element(element_fitness: float,
                           host_fitness: float) -> Tuple[float, float]:
    """
    Track #1: Self-preservation at gene level
    
    Transposons maximize their own copies
    Even if it harms the host
    
    Genes can be "selfish" - optimizing for themselves not organism
    """
    # Element spreads even if host suffers
    new_element_fitness = element_fitness * 1.1
    new_host_fitness = host_fitness * 0.95
    return new_element_fitness, new_host_fitness


def imprinting_conflict(maternal_allele: float,
                       paternal_allele: float) -> float:
    """
    Track #9d: Genetic conflict between parents
    
    Genomic Imprinting = parent-specific expression
    
    Mother's genes: conserve resources
    Father's genes: extract maximum from mother
    Same gene, opposite interests
    """
    # Simplified: conflicting optimization
    maternal_optimum = maternal_allele * 0.8  # Moderate growth
    paternal_optimum = paternal_allele * 1.2  # Maximum growth
    return (maternal_optimum + paternal_optimum) / 2


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GENOMICS & GENETICS - The Information Layer")
    print("Based on THE CATCH 44 Architecture")
    print("="*80 + "\n")
    
    print("THE INFORMATION STACK:")
    print("  • Biochemistry → molecular mechanisms")
    print("  • GENOMICS → code/information layer")
    print("  • Biology → functional organisms")
    print("  • Neuroscience → specialized substrate")
    print("  • Catch 44 → operating system")
    print("  • Linguistics → communication interface")
    print("\nFrom chemistry → code → life → mind → language")
    print("="*80 + "\n")
    
    # Information Density
    print("1. GENOMIC INFORMATION DENSITY (Track #2a)")
    human_density = genomic_information_density(coding_sequence=60_000_000,
                                               total_genome=3_000_000_000)
    print(f"   Human protein-coding: {human_density:.1%}")
    print("   Rest is regulatory, structural, evolutionary history")
    print("   → Quality over quantity in information storage\n")
    
    # Gene Networks
    print("2. GENE NETWORK EFFECT (Track #5: WE > I)")
    network_power = gene_network_effect(individual_gene=1,
                                       network_regulation=100)
    print(f"   Network regulation advantage: {network_power}x")
    print("   → No gene works alone, networks create function\n")
    
    # Genotype-Phenotype
    print("3. GENOTYPE-PHENOTYPE INTEGRITY (Track #0)")
    intact = genotype_phenotype_integrity("ATCG...", "functional_protein",
                                         {"temperature": 37, "pH": 7.4})
    print(f"   DNA sequence produces function: {intact}")
    print("   → Genotype is claim, phenotype is deed (context-dependent)\n")
    
    # Transcription Factor
    print("4. TRANSCRIPTION FACTOR INTERRUPT (Track #23: MOO)")
    baseline = transcription_factor_interrupt(baseline_expression=10,
                                             tf_binding=False,
                                             tf_strength=0)
    interrupted = transcription_factor_interrupt(baseline_expression=10,
                                                tf_binding=True,
                                                tf_strength=0.3)
    print(f"   Baseline expression: {baseline}")
    print(f"   TF repression: {interrupted}")
    print("   → Transcription factors interrupt gene expression\n")
    
    # Phenotype Emergence
    print("5. PHENOTYPE EMERGENCE (Track #67)")
    phenotype = phenotype_emergence(genotype={'gene1', 'gene2', 'gene3'},
                                   environment={'nutrition': 5, 'stress': 2},
                                   development_history=[1, 1.2, 1.5])
    print(f"   Phenotype complexity: {phenotype}")
    print("   → Organism emerges from genes × environment × history\n")
    
    # Genetic Code Redundancy
    print("6. GENETIC CODE REDUNDANCY (Track #6: Pair of Ducks)")
    leucine_codons = genetic_code_redundancy('Leucine')
    methionine_codons = genetic_code_redundancy('Methionine')
    print(f"   Leucine encoded by {leucine_codons} codons")
    print(f"   Methionine encoded by {methionine_codons} codon")
    print("   → Redundancy provides error tolerance\n")
    
    # Mutation vs Repair
    print("7. MUTATION VS REPAIR (Track #0: Replication Integrity)")
    high_fidelity = mutation_rate_vs_repair(errors_per_replication=100,
                                           repair_efficiency=0.99)
    low_fidelity = mutation_rate_vs_repair(errors_per_replication=100,
                                          repair_efficiency=0.80)
    print(f"   High-fidelity replication: {high_fidelity:.1f} errors survive")
    print(f"   Low-fidelity replication: {low_fidelity:.1f} errors survive")
    print("   → Balance: too few errors = no evolution, too many = death\n")
    
    # Epigenetic Memory
    print("8. EPIGENETIC MEMORY (Track #34: Memory without sequence change)")
    epi_memory = epigenetic_memory(dna_methylation=0.8,
                                   histone_modification=0.6,
                                   generations_maintained=3)
    print(f"   Epigenetic state maintained: {epi_memory:.2f}")
    print("   → Information layer on top of DNA sequence\n")
    
    # Alternative Splicing
    print("9. ALTERNATIVE SPLICING (Track #67: One gene, many proteins)")
    exons = ['exon1', 'exon2', 'exon3', 'exon4', 'exon5']
    factors = {'exon2': 0.3, 'exon4': 0.8}  # Context-dependent inclusion
    spliced = alternative_splicing(exons, factors)
    print(f"   Original exons: {len(exons)}")
    print(f"   Included in this context: {len(spliced)}")
    print("   → Same gene, different proteins via context\n")
    
    # Master Regulator
    print("10. MASTER REGULATOR CASCADE (Track #9d: Leverage)")
    cascade = master_regulator_cascade(master_gene=1.0,
                                      downstream_genes=500,
                                      amplification=0.3)
    print(f"   Master gene cascade effect: {cascade:.1f}x")
    print("   → Small change in master = massive phenotype shift\n")
    
    # Feedback Loops
    print("11. FEEDBACK LOOPS (Track #23: Regulation via MOO)")
    stable_a, stable_b = feedback_loop_stability(gene_a=5, gene_b=5,
                                                loop_type="negative")
    switch_a, switch_b = feedback_loop_stability(gene_a=5, gene_b=5,
                                                loop_type="positive")
    print(f"   Negative feedback (stability): A={stable_a:.2f}, B={stable_b:.2f}")
    print(f"   Positive feedback (switch): A={switch_a:.2f}, B={switch_b:.2f}")
    print("   → Network topology determines behavior\n")
    
    # Horizontal Gene Transfer
    print("12. HORIZONTAL GENE TRANSFER (Track #5: WE across species)")
    original = {'gene_a', 'gene_b'}
    donor = {'gene_c', 'gene_d', 'gene_e'}
    transferred = horizontal_gene_transfer(original, donor, transfer_rate=0.3)
    print(f"   Original genes: {len(original)}")
    print(f"   After HGT: {len(transferred)}")
    print("   → Bacteria share genes across species boundaries\n")
    
    # Drift vs Selection
    print("13. GENETIC DRIFT VS SELECTION (Track #8: Curve)")
    small_pop = genetic_drift_vs_selection(population_size=100,
                                          selection_coefficient=0.01,
                                          generations=100)
    large_pop = genetic_drift_vs_selection(population_size=1_000_000,
                                          selection_coefficient=0.01,
                                          generations=100)
    print(f"   Small population: {small_pop}")
    print(f"   Large population: {large_pop}")
    print("   → Some changes on a curve between random and selected\n")
    
    # Non-coding Function
    print("14. NON-CODING DNA FUNCTION (Track #2a: Quality over Quantity)")
    enhancer_func = non_coding_function("enhancer")
    print(f"   Enhancer functions: {enhancer_func}")
    print("   → 'Junk DNA' is regulatory, structural, evolutionary\n")
    
    # Genomic Imprinting
    print("15. GENOMIC IMPRINTING (Track #9d: Parent conflict)")
    offspring_growth = imprinting_conflict(maternal_allele=1.0,
                                          paternal_allele=1.0)
    print(f"   Offspring growth from conflicting interests: {offspring_growth:.2f}")
    print("   → Maternal genes conserve, paternal genes extract\n")
    
    print("="*80)
    print("CONCLUSION: Genomics as Information Architecture")
    print("\nThe genome isn't a blueprint - it's an INFORMATION SYSTEM:")
    print("  • Code with redundancy (error tolerance)")
    print("  • Networks not individuals (gene regulation)")
    print("  • Context determines output (genotype + environment)")
    print("  • Epigenetic memory (information beyond sequence)")
    print("  • 3D organization (spatial matters)")
    print("  • Conflicts within (selfish elements, parental battle)")
    print("\nSame Catch 44 engine running on molecular information:")
    print("  • Understanding = information density")
    print("  • WE > I = gene networks")
    print("  • Integrity = genotype matches phenotype")
    print("  • MOO = transcription factor interrupts")
    print("  • Emergence = genes × environment × development")
    print("\nGenomics completes the molecular → organismal bridge")
    print("="*80 + "\n")
    print("DAYENU - Framework #18 Complete")
    print("THE INFORMATION LAYER MAPPED")
    print("="*80)
