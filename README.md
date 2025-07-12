<div align="center">

# Oracles Bakery Mammet: ORB Discord Bot
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/Oracles-Bakery/ORBMammetBot)<br/>
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/Oracles-Bakery/ORBMammetBot?style=flat&labelColor=161616&color=00be5a)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/Oracles-Bakery/ORBMammetBot?style=flat&label=pull%20reqs&labelColor=161616&color=642d96)<br/>
![GitHub Issues or Pull Requests by label](https://img.shields.io/github/issues/Oracles-Bakery/ORBMammetBot/Premium%20Features?style=flat&label=Paid-Only%20Features&labelColor=%23161616&color=%23d5cb2b)
![GitHub Sponsors](https://img.shields.io/github/sponsors/VAMProductions?logo=githubsponsors&label=Github%20Sponsors&labelColor=161616&color=%23EA4AAA)

### _"Anything for the FC"_
</div>

This is the official repo for the Oracles Bakery Mammet, beloved son of Villicent and famously despised son of Villicent.<br/>
(It's a discord bot made to be always-free, with open and transparent code for the gang to all read through so they know they're safe, if you're looking for actual info)
---

## Quick Start

Looking to get the bot running for yourself? <br/>
Clone the repo and install dependencies, then it's ready to push to your (_totally_ made via V's referral link) [railway.com](https://github.com/sponsors/VAMProductions) environment!
```bash
git clone https://github.com/Oracles-Bakery/ORBMammetBot.git
cd ORBMammetBot
pip install -r requirements.txt
# Set up your .env file
python main.py
```
For help wiht your .env file you can check out [`settings.py`](settings.py) to see what environment pulls there are where you see `os.getenv()`.

---


# Feature Roadmap

Version numbers you see here are estimates, and are listed as X.Y.Z for `MAJOR.MINOR.FIX`<br/>
They'll be populated with numbers instead of letter when the order they'll be worked on is decided.<br/>
You can think of it like this:

`MAJOR` updates are things that REALLY expand the functionality, and I expect to be in version 1 for a long time, so I can make sure it all works. Version 2 will be when we break out of discord and have a website so people can use the bot with a prettier UI (So, you see, not any time soon.)<br/>
`MINOR` updates are new features, or, (hopefully never) the retirement of some features. A new channel for alerting you to free games is a nice feature, so it's a `MINOR` version update (because it's still all in the discord-bot only stage)<br/>
`FIX` updates are repairs and tweaks to things that already exist, and will more often than not be a group of updates all at once to make sure you're not getting updates spamming the merges. Current plan is to push all the fixes I have at 03:00 (that's 3am for you 12 hour enjoyers) UTC (server time for EU) every Monday (or "Sunday night" if you're so inclined.)

## Key
| Status | Meaning     | Details |
|-------:| ----------- | ------- |
| 🔴     | Blocked     | Something is missing to make this work |
| 🟠     | Backlog     | Priority shifted, expected later but soon! |
| 🟡     | Bughunt     | Likely made at 4am, recalled for bugfixing |
| 🟢     | Completed   | All done yippee woohoo yeehaw! |
| 🔵     | Planned     | Not the current workload, but coming eventually |
| 🟣     | In Progress | Current workload, only inside the fork V is working on |
| ⚪     | Idea        | Posited idea, awaiting feedback from GMs and FC members |
| ⚫     | Archived    | Rejected idea, will be worked on privately and pushed to sponsor repo |

## Roadmap
| Feature                                         | Target    | Status | Notes |
|-------------------------------------------------|:---------:|:------:| ----- |
| Dynamic Role Selection                          | v1.0.0    | 🟢    | Embed that dynamically loads roles and populates categories and lists for user role management |
| FFXIV Lodestone Character Verification          | v1.0.0    | 🟢    | Scraping implemented, basic embed currently |
| Basic Greeting Questions                        | v1.0.0    | 🟢    | Preferred name and favourite colour |
| Free Game Alerts                                | v1.1.0    | 🟣    | Free and discounted game alerts, and free weekend events |
| Support Tickets                                 | v1.Y.0    | 🔵    | Support requests and GM messaging system with transcript generation and isolated text channel creation |
| XIVAPI Implementation                           | v1.Y.0    | 🔵    | Find info about the items, quests, and anything else XIVAPI can provide! |
| Raid Helper                                     | v1.Y.0    | 🔵    | Setup for in-game events handling, with per-player class tracking and role assignment |
| FFXIV Server Updates                            | v1.Y.0    | 🔵    | Alerts about the FF servers for patch day and emergency maintenance |
| FFXIV Game Announcements                        | v1.Y.0    | 🔵    | Alerts about mogtome events, patch notes, etc... |
| Gear Calculator                                 | v1.Y.Z    | ⚪    | Feed an etro link of your current gear and the name of the content you want to do, and if you need any changes this will throw them back at you |
| Ocean Fishing Planner                           | v1.Y.Z    | ⚪    | If there's an algorithm to study, this will provide you with the route and bait requirements of an ocean fishing trip |
| FFXIV Server Alerts                             | v1.Y.Z    | ⚪    | Alerts to servers going back online on patch day, and emergency maintenance message from the devs |
| Teamcraft Integration                           | v1.Y.Z    | ⚪    | Characters you've claimed from the lodestone will be shown what parts of a project they can help |
| Retainer Reward Possibilities                   | v1.Y.Z    | ⚪    | List retainer venture rewards by job and level |
| Limited Job Helper                              | v1.Y.Z    | ⚪    | Help finding and grabbing all the different spells and quests for limited jobs |
| Gold Saucer Guides                              | v1.Y.Z    | ⚪    | Helpful guides on Triad rules, jumping puzzles, mini cactpot suggestions |
| XIV Timer Resets                                | v1.Y.Z    | ⚪    | Opt-in service for resets on Custom Delivery, Grand Company, Housing, Roulettes etc. |
| Discord web dashboard                           | v2.0.0    | 🔵    | All the features of version 1, now with a GUI! |
| Map Generator                                   | v2.Y.Z    | ⚪    | Get a map of a duty's loot chests, mob spawns, or an area's loot, gathering, or fate locations |
| Content Positioning Guides                      | v2.Y.Z    | ⚪    | Not sure where to stand for content? Enjoy a tasty guide for your role! |


<div align="center">
	<a href="github.com/Oracles-Bakery/ORBMammetBot">Oracles Bakery Mammet</a> © 2025 by <a href="github.com/VAMProductions">Villicent</a> is licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a><br/>
	<img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
	<img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
	<img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
	<img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
</div>
