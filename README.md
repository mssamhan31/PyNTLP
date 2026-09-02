# PyNTLP

## Executive Summary

`PyNTLP` stands for **Python for Network Tariff to Load Profile**.

PyNTLP is a Python tool for estimating how electricity network tariff designs
could change customer load profiles. In simpler terms, it helps answer:

> If a tariff encourages customers to use electricity at different times of day,
> what might the load profile look like afterwards?

The first implemented use case is the **Solar Sharer Offer (SSO)**. The broader
goal is for PyNTLP to become a reusable tool for modelling many network tariff
structures, not only SSO.

Contributor:

- M. Syahman Samhan
- m.samhan@unsw.edu.au

## Where This Project Is Up To

PyNTLP today implements one tariff, the Solar Sharer Offer, and it carries
substantial limitations that are set out in
[Assumptions and limitations](docs/assumptions-and-limitations.md). It should be
read as a first working example rather than a finished general tool.

The longer-term goal is for PyNTLP to model **any** tariff structure, not only
SSO. Getting there breaks into stages, and the first is the hardest: before you
can say how a tariff moves load, you have to know how much of the observed load
was ever flexible in the first place. Metered demand shows only a total, with
the flexible part already mixed into it.

**Stage one is Adaptive Quantile Flexibility (AQF)**, a method for estimating
that flexible component from aggregate data. The idea is that the quantile you
should use to separate flexible load from the underlying level is not a
hand-picked constant but a quantity you can compute, from how often flexible
events happen and how large they are. A conference paper describes this stage.

The code, data and figures behind that paper are in
[publication/1_conference/](publication/1_conference/) — see
[its README](publication/1_conference/README.md) for the model and how to
reproduce every result. It is standalone research code and is not imported by
the `pyntlp` package; if AQF proves out, its estimator logic will be ported into
the package as a separate, later effort.

## What Is The Solar Sharer Offer?

The Solar Sharer Offer is a network tariff concept that encourages eligible
customers to use more electricity during a defined daytime window, when solar
generation is more available on the local network.

The idea is not that customers necessarily use more electricity overall. Rather,
some flexible electricity use may move from one part of the day into another.
For example, customers might shift activities such as appliance use, electric
vehicle charging, or other flexible loads into the Solar Sharer window.

For planning and analysis, this means the original load profile needs to be
adjusted. PyNTLP helps estimate that adjustment.

## Current SSO Design Details

This summary reflects public Australian Government and Australian Energy
Regulator material available in May 2026. Check the official sources below
before using these details for customer-facing, regulatory, or commercial work.

The Solar Sharer Offer is planned to start on **1 July 2026** in areas covered
by the Default Market Offer.

Initial availability is for households in:

- New South Wales
- South Australia
- South East Queensland

It is not an Australia-wide offer at launch. In particular, "Queensland" here
means South East Queensland, not the whole state. Public government material
also says consideration is being given to making an SSO, or equivalent option,
available in other areas.

The free electricity window is expected to be:

- **11:00 am to 2:00 pm** in New South Wales
- **11:00 am to 2:00 pm** in South East Queensland
- **12:00 pm to 3:00 pm** in South Australia

The offer is designed as an opt-in tariff for households with smart meters.
Government material says it is intended to be available to households with or
without rooftop solar, and to both renters and homeowners.

The public design also includes a reasonable-use cap. Government material
describes this as access to up to **24 kWh** of free electricity during the
daily free-power window.

## Why This Tool Exists

Tariff design can influence when customers use electricity. Network planners,
tariff analysts, researchers, and engineers often need a repeatable way to test
those impacts.

PyNTLP aims to make that process clearer and more reusable by separating:

- the tariff assumptions
- the customer eligibility assumptions
- the load-profile adjustment logic
- the validation checks that help confirm the result is sensible

The SSO model is the first version of that workflow. Over time, the same
structure can be extended to other tariffs, such as different time-of-use,
demand, export, or location-based tariff designs.

## What PyNTLP Does

At a high level, PyNTLP:

- starts with an existing electricity load profile
- applies tariff and customer eligibility assumptions
- estimates how much load may move into the target tariff window
- removes the same amount of energy from other periods when the model assumes
  load is being shifted rather than created
- produces an adjusted profile effect that can be used for planning, reporting,
  and further analysis
- runs checks to help identify obvious issues in the output

The current SSO implementation focuses on daily load shifting into the Solar
Sharer window while keeping the modelled daily energy balanced.

For the current public SSO settings, this means PyNTLP models load that may move
into the free daytime period, especially **11:00 am to 2:00 pm** in New South
Wales and South East Queensland.

## What PyNTLP Is Not

PyNTLP is not:

- a billing system
- a customer pricing engine
- a tariff recommendation tool
- a replacement for customer research or behavioural trials
- a production data pipeline by itself
- a tool that decides whether any tariff is fair, optimal, or commercially
  appropriate

It is a modelling tool. Its role is to help estimate possible load-profile
impacts under stated assumptions.

## Current Status

The current package implements the first Solar Sharer Offer workflow.

The technical implementation can:

- load model assumptions from configuration
- calculate customer eligibility summaries
- estimate SSO-related load-profile changes
- apply participant caps so customer populations are not over-counted
- check that the modelled energy movement is balanced

Detailed implementation notes are kept in the `docs/` folder so this README can
stay readable for a broader audience.

## Who May Find This Useful

PyNTLP may be useful for:

- electricity network planners
- tariff and pricing analysts
- energy researchers
- forecasting teams
- data scientists and engineers supporting tariff modelling
- students or collaborators studying how tariffs may affect load profiles

## Documentation

For more detail, start with the [docs index](docs/README.md), or go directly to:

- [Glossary](docs/glossary.md)
- [Assumptions and limitations](docs/assumptions-and-limitations.md)
- [Usage guide](docs/usage-guide.md)
- [Model overview](docs/model-overview.md)
- [API contracts](docs/api-contracts.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Development notes](docs/development.md)
- [Repository structure](docs/repo-structure.md)

## References

Official sources for the public SSO description:

- [DCCEEW: Solar Sharer Offer to help cut electricity bills](https://www.dcceew.gov.au/about/news/solar-sharer-offer-help-cut-electricity-bills)
- [DCCEEW: Default Market Offer](https://www.dcceew.gov.au/energy/programs/default-market-offer)
- [AER: Default Market Offer 2026-27 review](https://www.aer.gov.au/industry/registers/resources/reviews/default-market-offer-2026-27)
- [AER: Draft Default Market Offer 2026-27 news release](https://www.aer.gov.au/news/articles/news-releases/aer-releases-draft-default-market-offer-2026-27)
- [AER: Solar Sharer Offer fact sheet for retailers](https://www.aer.gov.au/system/files/2026-03/Solar%20Sharer%20Offer%20-%20Fact%20Sheet%20for%20Retailers%20March%202026.pdf)

## For Developers

Install locally in editable mode:

```bash
pip install -e .[dev]
```

Run tests:

```bash
python -m pytest
```

Some tests use local Spark functionality and require Java. If Java is not
available, those tests are skipped and the pure Python tests still run.

The main package code lives in:

```text
src/pyntlp/
```

The detailed technical contract, including inputs, outputs, and validation
behaviour, is documented in [API contracts](docs/api-contracts.md).
