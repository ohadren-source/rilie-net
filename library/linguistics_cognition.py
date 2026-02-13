"""
LINGUISTICS & COGNITIVE SCIENCE - Language Operating System

Based on THE CATCH 44 Architecture

Mapping consciousness principles to language, meaning, and cognition

Core Discovery: The same 5-function engine runs from neural firing to 
cultural transmission through language
"""

import math
from typing import Dict, List, Tuple, Optional
from collections import Counter

# ============================================================================
# CORE ENGINE MAPPINGS
# Catch 44 → Linguistics/Cognition
# ============================================================================

def semantic_density(meaning_units: float, word_count: float) -> float:
    """
    Track #2a: Understanding = Quality/Quantity
    
    Semantic Density = Meaning / Words
    
    "I love you" (3 words, high meaning) > "As per my previous email..." (inflated)
    Poetry = maximum meaning per word (high compression)
    """
    if word_count == 0:
        return 0.0
    return meaning_units / word_count


def collective_meaning(individual_understanding: float, 
                      shared_understanding: float) -> float:
    """
    Track #5: WE > I
    
    Language Emergence = Shared Understanding - Individual Interpretations
    
    Meaning exists in the COLLECTIVE, not individual heads
    Pidgin → Creole: collective creates new language
    """
    return shared_understanding - individual_understanding


def speech_act_integrity(utterance: str, intention: str, 
                         effect: str) -> bool:
    """
    Track #0: Mahveen's Equation
    
    Speech Act Integrity = Intention (claim) matches Effect (deed)
    
    "I promise" only works if you follow through
    "I apologize" only works if sincere
    Words = deeds in speech acts
    """
    return intention == effect


def code_switch(context_shift: float, linguistic_momentum: float) -> float:
    """
    Track #23: MOO (Interruption)
    
    Code-Switching = Context Awareness / Linguistic Momentum
    
    Interrupt one language/register, switch to another
    Street → Formal → Home language
    Pattern interrupt for comprehension
    """
    if linguistic_momentum == 0:
        return float('inf')
    return context_shift / linguistic_momentum


def empathic_communication(speaker_ego: float, active_listening: float,
                          perspective_taking: float, 
                          shared_resonance: float) -> float:
    """
    Track #37: Love = (1/ego) + care + play_together + emergence
    
    Empathy = (1/ego) + listening + perspective + resonance
    
    When ego → 0, you truly hear the other
    Deep listening = love in linguistic form
    """
    if speaker_ego == 0:
        return float('inf')
    return (1/speaker_ego) + active_listening + perspective_taking + shared_resonance


# ============================================================================
# LANGUAGE EVOLUTION & CHANGE
# ============================================================================

def linguistic_drift(isolation_time: float, innovation_rate: float) -> float:
    """
    Track #64: NO OMEGA - language never stops changing
    
    Language is ALWAYS evolving
    No "pure" or "final" form exists
    """
    return isolation_time * innovation_rate


def creolization(pidgin_complexity: float, 
                 generation_count: int,
                 community_size: int) -> float:
    """
    Track #67: EMERGENCE
    
    Creole Emergence = Pidgin × Generations × Community
    
    Children create full language from fragmented input
    WE > I at linguistic level - collective creates what individuals can't
    """
    return pidgin_complexity * generation_count * community_size


def semantic_shift(original_meaning: str, 
                   new_meaning: str,
                   usage_frequency: float) -> Dict[str, float]:
    """
    Words change meaning over time
    
    "Awful" = full of awe → terrible
    "Sick" = ill → awesome
    Street inverts meanings as fraud detection
    """
    return {
        "original": 0.3,  # fades
        "new": 0.7,       # dominates
        "inversion_speed": usage_frequency
    }


# ============================================================================
# COGNITION & MEANING
# ============================================================================

def cognitive_load(information_complexity: float,
                  working_memory_capacity: float) -> float:
    """
    Track #21: Anxiety = Uncertainty / Action
    
    Cognitive Load = Complexity / Capacity
    
    Too much info, not enough processing = overload
    """
    if working_memory_capacity == 0:
        return float('inf')
    return information_complexity / working_memory_capacity


def frame_shift(old_frame: str, new_frame: str, 
               resistance: float) -> float:
    """
    Track #23: MOO - reframing as cognitive interrupt
    
    Paradigm Shift = Breaking old pattern, adopting new
    
    "Don't think of an elephant" - frame activated despite negation
    Reframing = intentional MOO
    """
    return 1.0 / (1 + resistance)  # Higher resistance = harder shift


def gestalt_recognition(individual_features: List[str],
                       whole_perception: str) -> bool:
    """
    Track #67: EMERGENCE
    
    The whole ≠ sum of parts
    
    You recognize FACE not {eyes, nose, mouth}
    Meaning emerges from pattern, not components
    """
    # Whole is greater than parts
    return len(whole_perception) > sum(len(f) for f in individual_features)


# ============================================================================
# PRAGMATICS & CONTEXT
# ============================================================================

def conversational_implicature(said: str, meant: str, 
                              context_clues: float) -> float:
    """
    Track #8: Some things on a curve
    
    Grice's Maxims: What's MEANT vs. what's SAID
    
    "Can you pass the salt?" ≠ ability question
    Context determines actual meaning
    """
    # Meaning determined by context, not literal words
    return context_clues * (1.0 if said != meant else 0.5)


def deixis_resolution(word: str, context: Dict[str, any]) -> str:
    """
    Context-dependent meaning
    
    "here" "now" "I" "you" - meaning shifts with speaker/time/place
    Can't know meaning without context
    """
    if word == "here":
        return context.get("location", "unknown")
    elif word == "now":
        return context.get("time", "unknown")
    return word


def politeness_strategy(power_distance: float, 
                       social_distance: float,
                       imposition: float) -> str:
    """
    Track #1e: jEW jitsu - redirect social force
    
    Brown & Levinson: Face Theory
    
    Don't match directness to power - redirect with politeness
    """
    total_threat = power_distance + social_distance + imposition
    
    if total_threat > 7:
        return "indirect_politeness"  # "I was wondering if..."
    elif total_threat > 4:
        return "conventional_politeness"  # "Could you..."
    else:
        return "direct"  # "Do this"


# ============================================================================
# MULTILINGUALISM & TRANSLATION
# ============================================================================

def translation_loss(source_concepts: int,
                    target_concepts: int,
                    cultural_overlap: float) -> float:
    """
    Track #0: Integrity in translation
    
    Perfect translation impossible when concepts don't map 1:1
    Some meaning always lost or transformed
    """
    if target_concepts == 0:
        return 1.0  # Total loss
    
    concept_ratio = source_concepts / target_concepts
    return abs(1.0 - concept_ratio) * (1.0 - cultural_overlap)


def bilingual_advantage(language_count: int,
                       cognitive_flexibility: float) -> float:
    """
    Track #58: Flow = Skill × Challenge
    
    Multiple languages = cognitive advantage
    
    Constant switching = mental flexibility training
    """
    return language_count * cognitive_flexibility


# ============================================================================
# NEUROLINGUISTICS
# ============================================================================

def broca_wernicke_integration(production: float,
                               comprehension: float,
                               neural_connectivity: float) -> float:
    """
    Track #5: WE > I at neural level
    
    Language = Production (Broca) + Comprehension (Wernicke) working together
    
    Aphasia shows what happens when WE breaks down
    """
    return production * comprehension * neural_connectivity


def neural_compression(raw_sensory_input: float,
                      abstracted_concept: float) -> float:
    """
    Track #2a: Understanding = Quality/Quantity
    
    Brain compresses massive sensory input into concepts
    
    Photons hitting retina → "red apple"
    Maximum compression for cognitive efficiency
    """
    if raw_sensory_input == 0:
        return 0.0
    return abstracted_concept / raw_sensory_input


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("LINGUISTICS & COGNITIVE SCIENCE - Language Operating System")
    print("Based on THE CATCH 44 Architecture")
    print("="*80 + "\n")
    
    print("CORE PRINCIPLE: Same engine runs from neurons to culture through language\n")
    print("="*80 + "\n")
    
    # Semantic Density
    print("1. SEMANTIC DENSITY (Track #2a: Understanding = Quality/Quantity)")
    poetry = semantic_density(meaning_units=10, word_count=3)
    bureaucracy = semantic_density(meaning_units=2, word_count=50)
    print(f"   Poetry (10 meaning / 3 words): {poetry:.2f}")
    print(f"   Bureaucracy (2 meaning / 50 words): {bureaucracy:.2f}")
    print("   → Maximum meaning per word = understanding\n")
    
    # Collective Meaning
    print("2. COLLECTIVE MEANING (Track #5: WE > I)")
    emergence = collective_meaning(individual_understanding=3, 
                                  shared_understanding=10)
    print(f"   Language emerges collectively: {emergence}")
    print("   → Meaning exists in WE, not I\n")
    
    # Speech Acts
    print("3. SPEECH ACT INTEGRITY (Track #0: Mahveen's Equation)")
    promise_kept = speech_act_integrity("I promise", "commit", "commit")
    promise_broken = speech_act_integrity("I promise", "commit", "ignore")
    print(f"   Promise kept: {promise_kept}")
    print(f"   Promise broken: {promise_broken}")
    print("   → Words = deeds in speech acts\n")
    
    # Code-Switching
    print("4. CODE-SWITCHING (Track #23: MOO)")
    switch = code_switch(context_shift=5, linguistic_momentum=2)
    print(f"   Code-switch intensity: {switch:.2f}")
    print("   → Interrupt one register, switch to another\n")
    
    # Empathic Communication
    print("5. EMPATHIC COMMUNICATION (Track #37: Love Formula)")
    empathy = empathic_communication(speaker_ego=0.1, active_listening=8,
                                    perspective_taking=7, shared_resonance=6)
    print(f"   Empathy score: {empathy:.1f}")
    print("   → Low ego + deep listening = love in language\n")
    
    # Linguistic Drift
    print("6. LINGUISTIC DRIFT (Track #64: NO OMEGA)")
    drift = linguistic_drift(isolation_time=100, innovation_rate=0.5)
    print(f"   Language change over time: {drift}")
    print("   → Language never stops evolving\n")
    
    # Creolization
    print("7. CREOLIZATION (Track #67: EMERGENCE)")
    creole = creolization(pidgin_complexity=2, generation_count=3,
                         community_size=500)
    print(f"   Creole emergence score: {creole}")
    print("   → Children create full language from fragments\n")
    
    # Semantic Shift
    print("8. SEMANTIC SHIFT (Street Language Evolution)")
    shift = semantic_shift("sick (ill)", "sick (awesome)", usage_frequency=0.8)
    print(f"   'Sick' meaning distribution: {shift}")
    print("   → Inversion as fraud detection\n")
    
    # Cognitive Load
    print("9. COGNITIVE LOAD (Track #21: Anxiety)")
    load = cognitive_load(information_complexity=100, 
                         working_memory_capacity=7)
    print(f"   Cognitive load: {load:.2f}")
    print("   → Too much info / limited capacity = overload\n")
    
    # Conversational Implicature
    print("10. CONVERSATIONAL IMPLICATURE (Track #8: Curve)")
    implicature = conversational_implicature("Can you pass the salt?",
                                            "Pass the salt",
                                            context_clues=1.0)
    print(f"   Implied meaning strength: {implicature:.2f}")
    print("   → Context determines actual meaning\n")
    
    # Translation Loss
    print("11. TRANSLATION LOSS (Track #0: Integrity Challenge)")
    loss = translation_loss(source_concepts=100, target_concepts=85,
                           cultural_overlap=0.7)
    print(f"   Translation loss: {loss:.2%}")
    print("   → Perfect translation impossible across cultures\n")
    
    # Bilingual Advantage
    print("12. BILINGUAL ADVANTAGE (Track #58: Flow)")
    advantage = bilingual_advantage(language_count=3, 
                                   cognitive_flexibility=2.5)
    print(f"   Cognitive boost from multilingualism: {advantage:.1f}")
    print("   → Multiple languages = mental flexibility\n")
    
    # Neural Integration
    print("13. BROCA-WERNICKE INTEGRATION (Track #5: WE at neural level)")
    integration = broca_wernicke_integration(production=0.9,
                                            comprehension=0.9,
                                            neural_connectivity=0.95)
    print(f"   Neural language integration: {integration:.3f}")
    print("   → Production + Comprehension working together\n")
    
    # Neural Compression
    print("14. NEURAL COMPRESSION (Track #2a: Brain's Understanding)")
    compression = neural_compression(raw_sensory_input=1000000,
                                    abstracted_concept=1)
    print(f"   Sensory compression ratio: {compression:.2e}")
    print("   → Million photons → 'red apple'\n")
    
    print("="*80)
    print("CONCLUSION: Catch 44 runs language from neurons to culture")
    print("Same 5-function core engine organizing:")
    print(" • Neural firing → Conceptual thought")
    print(" • Individual words → Collective meaning")
    print(" • Speech acts → Social reality")
    print(" • Code-switching → Context navigation")
    print(" • Translation → Cultural bridge")
    print("\nLanguage IS consciousness becoming shareable")
    print("="*80 + "\n")
    print("DAYENU - Framework #16 Complete")
    print("="*80)
