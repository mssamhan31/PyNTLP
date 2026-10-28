---
title: Home
hide:
  - navigation
  - toc
---

<section class="ntlp-landing">

<header class="ntlp-hero">
  <p class="ntlp-eyebrow">Python for Network: Tariff to Load Profile (PyNTLP)</p>
  <h1>Three hours of free electricity a day is something no load forecast has seen before.</h1>
  <p class="ntlp-lead">Since July 2026, households in parts of Australia can choose a plan that makes
  electricity free from 11:00 to 14:00 every day<span class="ntlp-ref">[1]</span>. Network forecasts
  learn from years of history, and none of that history contains a standing free window. PyNTLP is
  open-source software that turns a tariff like this into a change to the load profile a forecast
  can use.</p>
  <div class="ntlp-actions">
    <a class="ntlp-button ntlp-button--primary" href="overview/">Get started</a>
    <a class="ntlp-button" href="#the-question">The research question</a>
    <a class="ntlp-button" href="https://github.com/mssamhan31/PyNTLP">View on GitHub</a>
  </div>
</header>

<section class="ntlp-section ntlp-split">
  <div>
    <p class="ntlp-eyebrow">The problem</p>
    <h2>A forecast learns from history, and the history has no free window</h2>
    <p>Electricity networks forecast net load, the power their customers draw from the grid less
    what rooftop solar sends back, to plan the network and decide where to invest. These forecasts
    learn from years of past readings, weather and the calendar, and assume the future will look
    like the past.</p>
    <p>A new tariff breaks that assumption. When a whole region can use electricity for free in the
    same three hours every day, load in those hours can change in ways the history cannot show. It
    is a structural break, and a forecaster needs to know what happens inside the window before
    adjusting for it.</p>
  </div>
  <figure class="ntlp-day" aria-label="One day from midnight to midnight, with 11:00 to 14:00 marked as the free window and three questions about it.">
    <div class="ntlp-day-label"><span>Free window, 11:00 to 14:00</span></div>
    <div class="ntlp-day-track"><div class="ntlp-day-window">?</div></div>
    <div class="ntlp-day-scale">
      <span style="left: 0%">00:00</span>
      <span style="left: 25%">06:00</span>
      <span style="left: 50%">12:00</span>
      <span style="left: 75%">18:00</span>
      <span style="left: 100%">24:00</span>
    </div>
    <ul class="ntlp-day-questions">
      <li>What does load do in these three hours?</li>
      <li>Which households respond?</li>
      <li>How should a forecast allocate it?</li>
    </ul>
    <figcaption>One day under the Solar Sharer Offer in Ausgrid's area. The tariff fixes the free
    window; what load does inside it is the open question.</figcaption>
  </figure>
</section>

<section class="ntlp-section ntlp-facts">
  <p class="ntlp-eyebrow">Key facts</p>
  <h2>Two policies, one year apart</h2>
  <div class="ntlp-stats">
    <div class="ntlp-stat"><strong>3 hours</strong><span>of free electricity a day on the Solar Sharer Offer, 11:00 to 14:00 in New South Wales<span class="ntlp-ref">[1,&nbsp;2]</span></span></div>
    <div class="ntlp-stat"><strong>1 July 2026</strong><span>the Solar Sharer Offer became available in New South Wales, South East Queensland and South Australia<span class="ntlp-ref">[1]</span></span></div>
    <div class="ntlp-stat"><strong>1 July 2025</strong><span>the Cheaper Home Batteries Program began, a year earlier<span class="ntlp-ref">[3]</span></span></div>
    <div class="ntlp-stat"><strong>About 30%</strong><span>off the upfront cost of a home battery installed with rooftop solar, under that program<span class="ntlp-ref">[4]</span></span></div>
    <div class="ntlp-stat"><strong>1.8 million</strong><span>customers in Ausgrid's network across Sydney, the Central Coast and the Hunter, about 1.5 million of them homes<span class="ntlp-ref">[5]</span></span></div>
  </div>
  <p class="ntlp-note">Retailers were selling free midday plans before the Solar Sharer Offer began,
  such as OVO Energy's Free 3 and GloBird Energy's ZeroHero, both free from 11:00 to
  14:00<span class="ntlp-ref">[6,&nbsp;7]</span>.</p>
</section>

<section class="ntlp-section">
  <p class="ntlp-eyebrow">Why it matters</p>
  <h2>Today's estimates are assumptions, not measurements</h2>
  <div class="ntlp-cards ntlp-cards--four">
    <div class="ntlp-card">
      <h3>Forecasts learn from history</h3>
      <p>A tariff that was never in force leaves no trace in past readings, so a forecast trained on
      them cannot learn its effect.</p>
    </div>
    <div class="ntlp-card">
      <h3>Estimates assume a share</h3>
      <p>The government's impact analysis assumed households would move a share of their
      electricity use, 10 to 30%, into the window<span class="ntlp-ref">[8]</span>.</p>
    </div>
    <div class="ntlp-card">
      <h3>Elasticity breaks at zero</h3>
      <p>Economic models move load in proportion to the percentage change in
      price<span class="ntlp-ref">[9]</span>. When the price falls to zero, that percentage is
      undefined.</p>
    </div>
    <div class="ntlp-card">
      <h3>Nobody has measured it</h3>
      <p>What load actually does in a standing daily free window has not been measured; the first
      study of the scheme lists the actual load-shift curves as unknown<span class="ntlp-ref">[10]</span>.</p>
    </div>
  </div>
  <p>Networks plan for peak and minimum demand years ahead, so the question cannot wait for the
  history to catch up.</p>
</section>

<section class="ntlp-section" id="the-question">
  <p class="ntlp-eyebrow">The research question</p>
  <h2>Three questions about one free window</h2>
  <p class="ntlp-question">What happens to load inside the window, which households respond, and how
  should a forecast allocate the change across the window?</p>
  <p>A journal article in preparation answers them with smart-meter data from Ausgrid's network,
  in three steps.</p>
  <div class="ntlp-steps">
    <div class="ntlp-step">
      <h3>Measure</h3>
      <p>Measure the load response to a standing daily free window from half-hourly smart-meter
      readings, across Ausgrid's network.</p>
    </div>
    <div class="ntlp-step">
      <h3>Attribute</h3>
      <p>Compare groups of households defined from Ausgrid's register of rooftop solar and other
      distributed energy resources, to find where the response comes from.</p>
    </div>
    <div class="ntlp-step">
      <h3>Model</h3>
      <p>Build a model that allocates the response inside the window, and test it against the
      allocations forecasters use today.</p>
    </div>
  </div>
  <p class="ntlp-note">The findings will appear with the article.</p>
</section>

<section class="ntlp-section ntlp-aside">
  <p class="ntlp-eyebrow">A separate study</p>
  <h2>Adaptive Quantile Flexibility (AQF)</h2>
  <p>AQF is a separate piece of research, not part of the PyNTLP package. It asks how much of an
  aggregate load profile is flexible without hand-picking a quantile to split it.</p>
  <p>At each time of day, AQF fits two Gaussian curves to the daily readings and computes from that
  fit the quantile that lands on the underlying load, with a test that flags the times when the two
  cannot be told apart.</p>
  <p>On synthetic data, AQF cut the error in the estimated underlying load to about a third of the
  best fixed quantile's, about halved the median error in recovered flexible energy, and came close
  to an oracle that knows the true quantile wherever the separation test was
  met<span class="ntlp-ref">[11]</span>.</p>
  <div class="ntlp-actions">
    <a class="ntlp-button" href="aqf/">About AQF</a>
    <a class="ntlp-button" href="https://github.com/mssamhan31/PyNTLP/tree/main/publication/1_conference">AQF code</a>
  </div>
</section>

<section class="ntlp-section">
  <p class="ntlp-eyebrow">Research</p>
  <h2>Built on a PhD study with Ausgrid</h2>
  <p>PyNTLP grows out of a PhD study at UNSW Sydney in partnership with Ausgrid's Demand Forecasting
  team. A journal article on the Solar Sharer Offer is in preparation. The separate AQF study is
  accepted for the 2026 IEEE PES Innovative Smart Grid Technologies Asia
  conference<span class="ntlp-ref">[11]</span>.</p>
  <div class="ntlp-actions">
    <a class="ntlp-button" href="papers/">Papers and citation</a>
    <a class="ntlp-button" href="https://doi.org/10.5281/zenodo.22246959">Software DOI</a>
  </div>
</section>

<section class="ntlp-section">
  <p class="ntlp-eyebrow">The team</p>
  <h2>Who made it</h2>
  <div class="ntlp-team">
    <div class="ntlp-card">
      <h3>UNSW Sydney</h3>
      <p>M. Syahman Samhan, Anna Bruce and Baran Yildiz, School of Photovoltaic and Renewable
      Energy Engineering</p>
    </div>
    <div class="ntlp-card">
      <h3>Ausgrid</h3>
      <p>Navid Haghdadi and Daniel Sim, Demand Forecasting</p>
    </div>
  </div>
  <p class="ntlp-small">PyNTLP is part of M. Syahman Samhan's PhD study, supported by the University
  International Postgraduate Award (UIPA) from UNSW and top-up scholarships from Ausgrid, RACE for
  2030 and the NSW Decarbonisation Innovation Hub. It is open source under the MIT licence.</p>
</section>

<section class="ntlp-section">
  <p class="ntlp-eyebrow">References</p>
  <ol class="ntlp-references">
    <li>Australian Energy Regulator, "The Solar Sharer Offer (SSO): What you need to know," Energy
    Made Easy, last updated 30 June 2026.
    <a href="https://www.energymadeeasy.gov.au/hot-topics/solar-sharer-offer-what-you-need-to-know">energymadeeasy.gov.au</a></li>
    <li>Department of Climate Change, Energy, the Environment and Water, "Energy plan now provides
    daily free-power window," 1 July 2026.
    <a href="https://www.dcceew.gov.au/about/news/energy-plan-now-provides-daily-free-power-window">dcceew.gov.au</a></li>
    <li>Clean Energy Regulator, "Small-scale Renewable Energy Scheme," Quarterly Carbon Market
    Report, December quarter 2025, last updated 5 March 2026.
    <a href="https://cer.gov.au/markets/reports-and-data/quarterly-carbon-market-reports/quarterly-carbon-market-report-december-quarter-2025/small-scale-renewable-energy-scheme">cer.gov.au</a></li>
    <li>Clean Energy Regulator, "Solar batteries," last updated 31 July 2026.
    <a href="https://cer.gov.au/schemes/renewable-energy-target/small-scale-renewable-energy-scheme/small-scale-renewable-energy-systems/solar-batteries">cer.gov.au</a></li>
    <li>Ausgrid, "Distribution and Transmission Annual Planning Report," December 2025, pp. 6
    and 14.
    <a href="https://www.ausgrid.com.au/about-us/regulation-and-compliance/network-planning/dtapr">ausgrid.com.au</a></li>
    <li>OVO Energy, "The Free 3 plan."
    <a href="https://pages.ovoenergy.com.au/the-free-3-plan">ovoenergy.com.au</a></li>
    <li>GloBird Energy, "ZeroHero."
    <a href="https://www.globirdenergy.com.au/energy-saver/zerohero/">globirdenergy.com.au</a></li>
    <li>Department of Climate Change, Energy, the Environment and Water, "Options to Provide Solar
    Sharer Offer: Impact Analysis (Second Pass)," Office of Impact Analysis, 2026.
    <a href="https://oia.pmc.gov.au/published-impact-analyses-and-reports/options-provide-solar-sharer-offer">oia.pmc.gov.au</a></li>
    <li>D. S. Kirschen, G. Strbac, P. Cumperayot and D. de Paiva Mendes, "Factoring the elasticity
    of demand in electricity prices," IEEE Transactions on Power Systems, vol. 15,
    pp. 612–617, 2000.
    <a href="https://doi.org/10.1109/59.867149">doi.org/10.1109/59.867149</a></li>
    <li>R. Galvin, "Free midday electricity in a Solar Sharer scheme: Should Germany follow
    Australia's lead?," Renewable Energy, vol. 267, 125735, 2026.
    <a href="https://doi.org/10.1016/j.renene.2026.125735">doi.org/10.1016/j.renene.2026.125735</a></li>
    <li>M. S. Samhan, N. Haghdadi, D. Sim, A. Bruce and B. Yildiz, "Adaptive Quantile Flexibility:
    Recovering Candidate Flexible Load from Aggregate Profiles for Network Tariff Modelling,"
    accepted for the 2026 IEEE PES Innovative Smart Grid Technologies Asia (ISGT Asia), Wuhan,
    China, 30 October to 1 November 2026.</li>
  </ol>
</section>

</section>
