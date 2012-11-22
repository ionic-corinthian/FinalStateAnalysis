'''

Build a version of the MVA MET recipe which runs only on objects in
the UW PAT tuple.

Author: Evan K. Friis, UW Madison

'''

import FWCore.ParameterSet.Config as cms

try:
    from JetMETCorrections.METPUSubtraction.mvaPFMET_leptons_cff import \
        calibratedAK5PFJetsForPFMEtMVA, pfMEtMVA, \
        isomuons, isoelectrons

    # Modify muons
    muon_cut = isomuons.cut
    isomuons = cms.EDFilter(
        "PATMuonSelector",
        src=cms.InputTag("cleanPatMuons"),
        cut=muon_cut,
        filter=cms.bool(False)
    )
    # Modify electrons
    e_cut = isoelectrons.cut
    isoelectrons = cms.EDFilter(
        "PATMuonSelector",
        src=cms.InputTag("cleanPatElectrons"),
        cut=e_cut,
        filter=cms.bool(False)
    )
    # Modify taus
    isotaus = cms.EDFilter(
        "PATTauSelector",
        src=cms.InputTag("selectedPatTaus"),
        cut=cms.string(
            'pt > 19 && abs(eta) < 2.3 && '
            'tauID("decayModeFinding") && '
            'tauID("byIsolationMVAraw") > 0.7 && '
            'tauID("againstElectronLoose") && tauID("againstMuonLoose")'),
        filter=cms.bool(False)
    )

    pfMEtMVAsequence = cms.Sequence(
        calibratedAK5PFJetsForPFMEtMVA *
        isomuons * isoelectrons * isotaus *
        pfMEtMVA
    )
except ImportError:
    import sys
    sys.stderr.write(
        "Warning: MVA MET dependencies not installed => MVA MET disabled.\n")
    pfMEtMVAsequence = cms.Sequence()
