# Revision 2026 of ICG-26-0040: data and code

This folder contains everything behind the revised manuscript *Decisive but Safe: Win–Draw–Loss Nugget Positions in Engine Chess* (A. Manzo, A. Ambanelli, P. Ciancarini, A. Palla), submitted to the ICGA Journal. The working notes, scripts and pre-registration documents are in Italian. This index is in English.

## Phases, data and pre-registration

Every match, tournament and oracle comparison was designed in a commit made before its first game or analysis.

| Phase | What | Results folder (`risultati/`) | Pre-registration | Report (`rapporti/`) |
|---|---|---|---|---|
| A | Extraction from World Championship games, Stockfish 19, 60 s | registries in `registri/` | none: selection rules fixed in `68221a7` | `stabilita_2026.md` |
| A3 | Two more analyses of the 2,321 candidates (noise) | registries in `registri/` | none: selection rules fixed in `68221a7` | `stabilita_2026.md` |
| C | Primary match, ShashChess 42.3 vs Stockfish 19, pool of 130, 25'+10" | `20261118_2057_pool_robusto` | `68221a7` | `statistiche_pool_robusto.md` (in the results folder), `s5_c.json` |
| D | Round robin of four engines, Top-100, 25'+10" | `20261120_0014_rr_top100_robusto` | `9d17f90` | `rapporto_roundrobin_2026.md` |
| E3 | Nodes per second under full load | `20261121_1027_nps_2026` | `a2167cb` | `rapporto_E3_E4.md` |
| E4 | Pool of 130 at 60"+0.6" | `20261121_1045_pool_tc60` | `a2167cb` | `rapporto_E3_E4.md` |
| E1 | 250 UHO openings with the nuggets' Pwin, 25'+10" | `20261121_1156_controllo_uho` | `a2167cb` | `rapporto_E1_B.md` |
| B | Second oracle: Lc0 v0.32.1 on the 2,321 candidates | `registri/lc0_tutte_le_posizioni.csv.gz` | `7ca61d3` | `rapporto_E1_B.md` |
| E5 | Pool of 130 at 60'+30" | `20261122_0324_pool_tc3600` | `7ca61d3` | `rapporto_E5.md` |
| F | 320 new positions with Pfav from 0.55 to 0.95, one colour-reversed pair each, 25'+10" | `20261122_2211_fasce_tc1500` | `47d6a0b` | `rapporto_F.md` |

Pre-registration documents: `PREREGISTRAZIONE_match_C.md`, `PREREGISTRAZIONE_roundrobin.md`, `PREREGISTRAZIONE_E1_E4.md`, `PREREGISTRAZIONE_B_E5.md`, `PREREGISTRAZIONE_F.md`.

The logs of the overnight queues that ran the phases are in `risultati/diari/`.

Each results folder holds:

- the games (`partite*.pgn.gz`) and the cutechess-cli logs;
- the exact command (`comando*.txt`) and the scripts used;
- the positions (`.epd`);
- the description of the machine (`macchina.txt`);
- the SHA-256 checksum and bench signature of every engine (`motori.txt`).

## Positions (`posizioni/`)

- `medie_3analisi.csv`: the 2,321 candidates, with the mean, standard deviation and best moves of three analyses.
- `nuggets_pool_robusto.{csv,epd}`: the pool of 130 robust nuggets, one per game line.
- `nuggets_top100_robusto.{csv,epd}`: the Top-100, the pool positions with the lowest ΔWDL.
- `uho_screening_1200*`, `uho_250.*`: screening and selection of the UHO control set.
- `fasce_candidate.csv`: the 360 new candidates of the outer bands of phase F (`preseleziona_fasce.py`).
- `fasce_320.{csv,epd,md}`: the 320 positions of phase F, 80 per band of Pfav (`seleziona_fasce.py`, seed 2026).

## Registries (`registri/`, gzip)

- `wch.pgn.gz` and `estrazione_pgn_sha256.txt`: the source games.
- `estrazione_*`: one analysis of each of the 85,491 distinct positions.
- `rumore_run01/02.csv.gz`: two more analyses of the candidates.
- `uho_rianalisi01/02.csv.gz`: two more analyses of the 250 UHO positions.
- `lc0_tutte_le_posizioni.csv.gz`: the Lc0 analysis of the candidates.
- `fasce_rianalisi01/02.csv.gz`: two more analyses of the 360 new candidates of phase F.

## Recomputing the numbers of the paper

The statistics scripts read plain-text PGN files. First run `gunzip -k risultati/*/*.pgn.gz` from this folder. Note that `*.pgn` is ignored by git.

- `statistiche_match.py`: match and round-robin statistics. Pentanomial Elo, errors clustered by position, McNemar's test, Bradley–Terry with bootstrap, and the interaction between two experiments (`--confronta`).
- `statistiche_rr_extra.py`: decisive games, games won by the unfavoured side, conversion rates, decisive share by Pwin band.
- `confronto_nugget_uho.py`: nuggets against UHO openings, with logistic regressions clustered by position.
- `confronto_lc0.py`: agreement between Stockfish and Lc0.
- `analisi_articolo.py`: produces three results:
  - ShashChess − Stockfish by Pwin band (Table 5);
  - the common logistic fit of decisive games on Pwin (Figure 4);
  - the composition of the selected sets (Section 4).
- `analisi_f.py`: the pre-registered analyses of phase F (Table 7): the slope of the ShashChess pair score on Pfav with robust standard errors, the Elo difference, the decisive share and the safety of the favoured side by band, and the exploratory split by Shashin zone.
- `confronto_f_nugget.py`: phase F against the nuggets at equal Pfav (exploratory, Section 6.8).

Example:

```bash
python analisi_articolo.py --c risultati/20261118_2057_pool_robusto --d risultati/20261120_0014_rr_top100_robusto \
  --e1 risultati/20261121_1156_controllo_uho --e4 risultati/20261121_1045_pool_tc60 \
  --uho-registri posizioni/uho_250.csv registri/uho_rianalisi01.csv.gz registri/uho_rianalisi02.csv.gz \
  --posizioni posizioni --out rapporti/analisi_articolo
```

The commands for phase F are at the top of `rapporti/rapporto_F.md`.

## Platform

- Two Intel Xeon 6972P processors: 192 physical cores, SMT disabled, six NUMA nodes.
- 1.5 TB of memory, Ubuntu Linux with kernel 6.8, cutechess-cli 1.5.1.
- 47 games at a time, each engine with 4 threads and 2 GB of hash.
- Syzygy tablebases; engines restarted before every game.
- The platform was provided by Intel.
