# civics.py - DIP 3,6,9 Civics Domain for RILIE
# Domains: Government, Rights, Voting, Civic Duty, Fairness

CIVICS_KNOWLEDGE = {
    "government": {
        "compression": [
            "Federalism power distribution between levels prevents single-point failure",
            "Checks and balances structural antagonism maintains equilibrium",
            "Three branches designed for deliberate friction, not efficiency",
            "Bicameral legislature deliberate slowdown for deliberation",
            "Executive veto power calibrated tension with legislative intent"
        ],
        "fairness": [
            "Equal protection clause structural guarantee against arbitrary classification",
            "Due process substantive and procedural dual protection against state overreach",
            "Commerce clause tension between federal power and state sovereignty",
            "Enumerated powers strict limits on federal authority by design",
            "Tenth Amendment residual powers reserved to states by default"
        ]
    },
    "rights": {
        "compression": [
            "First Amendment speech protection absolute except narrow compelling interests",
            "Second Amendment individual right confirmed post-Heller, nuanced carry restrictions",
            "Fourth Amendment warrant requirement calibrated privacy vs security",
            "Fifth Amendment self-incrimination calibrated truth-seeking vs coercion",
            "Fourteenth Amendment incorporation made Bill of Rights applicable to states"
        ],
        "love": [
            "Ninth Amendment unenumerated rights doctrine preserves natural rights framework",
            "Privileges and Immunities Clause fundamental rights protection across states",
            "Equal Protection intermediate scrutiny calibrated gender classifications",
            "Substantive Due Process penumbral rights privacy, marriage, contraception",
            "Fundamental rights trigger strict scrutiny highest protection level"
        ],
        "fear": [
            "Police power state authority limited by enumerated constraints",
            "Ex post facto laws prohibited retrospective criminalization",
            "Bill of attainder direct legislative punishment forbidden",
            "Habeas corpus suspension only rebellion/invasion narrow exception",
            "Quartering prohibited peacetime standing army control"
        ]
    },
    "voting": {
        "compression": [
            "Electoral College calibrated large state advantage with small state protection",
            "Senate equal state representation deliberate check on majority tyranny",
            "House proportional representation calibrated population democracy",
            "Representative democracy calibrated direct democracy chaos prevention",
            "FEC campaign finance calibrated free speech vs corruption prevention"
        ],
        "fairness": [
            "One person one vote calibrated equal representation principle",
            "Voting Rights Act calibrated access vs fraud prevention tension",
            "Gerrymandering calibrated competitive districts vs community preservation",
            "Voter ID calibrated integrity vs access calibrated friction",
            "Ranked choice voting calibrated majority preference vs plurality winner"
        ]
    },
    "civic": {
        "compression": [
            "Jury nullification calibrated community standards vs strict law application",
            "Grand jury indictment calibrated prosecutorial power check",
            "Impeachment calibrated political remedy for high crimes",
            "Censure calibrated formal disapproval without removal",
            "Recall election calibrated voter remedy for elected misconduct"
        ],
        "fairness": [
            "Sunshine laws calibrated transparency vs executive privilege",
            "FOIA calibrated public right vs national security calibrated exemptions",
            "Whistleblower protection calibrated truth-telling vs loyalty",
            "Inspector General calibrated internal oversight vs chain of command",
            "Ombudsman calibrated citizen advocate vs bureaucratic inertia"
        ]
    }
}

def civics_domains(stimulus: str) -> list[str]:
    """Detect civics subdomains"""
    domain_keywords = {
        "government": ["federalism", "checks", "branches", "senate", "veto"],
        "rights": ["amendment", "due process", "equal protection", "warrant", "self-incrimination"],
        "voting": ["electoral", "gerrymander", "voter id", "ranked choice", "one person"],
        "civic": ["jury", "impeach", "whistleblower", "sunshine", "ombudsman"]
    }
    stimulus_lower = stimulus.lower()
    scores = {domain: sum(1 for kw in kws if kw in stimulus_lower) for domain, kws in domain_keywords.items()}
    return sorted(scores, key=scores.get, reverse=True)[:3]

# Priority signals tuned for civics (anti-beige + structural tension focus)
CIVICS_AMUSING_SIGNALS = ["gerrymander", "pork", "lame duck", "filibuster", "pocket veto"]
CIVICS_INSIGHTFUL_SIGNALS = ["federalism", "enumerated", "tenth amendment", "commerce clause"]
CIVICS_NOURISHING_SIGNALS = ["civic duty", "jury service", "vote", "deliberation"]
CIVICS_COMPASSIONATE_SIGNALS = ["equal protection", "due process", "fundamental rights"]
CIVICS_STRATEGIC_SIGNALS = ["supreme court", "precedent", "strict scrutiny", "intermediate scrutiny"]

# Reject signals (beige civics)
CIVICS_REJECT_SIGNALS = ["taxes are theft", "government bad", "freedom", "tyranny"]  # Pure sloganeering

# Integrate into RILIE DOMAINKNOWLEDGE (commented out — DOMAINKNOWLEDGE not available at module load)
# DOMAINKNOWLEDGE["civics"] = CIVICS_KNOWLEDGE

if __name__ == "__main__":
    print("CIVICS DOMAIN LOADED")
    print("Domains:", civics_domains("What is gerrymandering?"))
    print("Sample knowledge:", list(CIVICS_KNOWLEDGE["rights"]["fairness"])[:2])
