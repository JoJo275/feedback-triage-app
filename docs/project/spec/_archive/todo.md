# Answers to Divergence between core-idea.md and spec-v2.md

-	Recommendations on how we should position this app? Would it be a SaaS/B2B? I feel like it would and I feel like it would be helpful to have this written down even though this is only a portfolio app.
-	Everything in vs regarding question one. I guess I’ll just break it up linearly if the pr grows too large.
-	Regarding D2, do we have two data types for a card already: pain level and priority level? Should we have two? I feel like both could be helpful with having a pain level for the customer and then a priority level for the team. Do whatever you recommend in this scenario.
-	Regarding D3, I like your recommendation but when someone chooses “other”, can they input whatever value they want? I feel like that would be helpful. Implement it if you recommend it.
-	Regarding D4, what are lookup tables? Same thing for “other” here as well. If you recommend being able to input whatever value someone wants when “other” is chosen, implement it. If you recommend adding lookup tables, add them.
-	Regarding D5, Here’s more concrete information:
role setup for app
Admin:
  You. Full access.

Public submitter:
  Anyone who submits feedback. No account required.

Demo user:
  Optional login for portfolio reviewers. Limited access.

Workspace owner:
  Person/company using SignalNest.

Team member:
  Someone invited by the owner.

Submitter/customer:
  Person giving feedback.

Dashboard:
Dashboard
inbox
Feedback
Submitters
Roadmap
Changelog
Insights
Settings

Add Submitters only when you actually show useful submitter info, like: (and I want to actually show useful submitter info.)
Submitter page feature	Why useful
Email/name	Know who sent feedback
Feedback history	See repeated complaints/requests
Last submitted date	Understand recency
Number of submissions	Spot high-signal users
Status of their items	Follow up later
Internal notes	Track context
Important product decision
Do not require public users to create accounts just to submit feedback unless there is a strong reason.
For a feedback tool, this is better:
Submit feedback:
  Name optional
  Email optional or required
  Message required
  No account required
Require accounts only for people who manage the feedback dashboard.
Final recommendation
For SignalNest:
Primary users:
  builders, indie hackers, product teams, support teams

Admins:
  workspace owners/team leads who manage the feedback system

Submitters:
  customers, testers, visitors, users who send feedback


When Tags deserves its own nav item (I want to implement tags and the following functions)
Give Tags a main nav section only if it becomes an insights/organization feature, not just a settings list.
If Tags page only does this	Put it in Settings
Create tag
Rename tag
Delete tag
Pick tag color
Merge duplicate tags
If Tags page does this	Main nav can make sense
Shows top tags by volume
Shows trends over time
Shows unresolved feedback by tag
Shows tag health/cleanup suggestions
Lets users browse feedback by product area
Acts like a category dashboard
Better label if it is a main nav item
If you want it to be more than tag management, call it something like:
Label	Meaning
Topics	More user-friendly than Tags
Categories	Good if tags are broad product areas
Signals	Brand-aligned, but could be vague
Insights	Best if it includes trends and analytics
Tags	Best if it is literal tag management
Inside Insights, tags become useful:
Section	What it shows
Top topics	Most common tags
Rising topics	Tags increasing recently
Pain points	Tags with most complaints/bugs
Planned by topic	Tags connected to planned roadmap items
Unresolved by topic	Where backlog is building up

Simple distinction
Page	Meaning	What it shows
Inbox	The triage queue	New, unreviewed, needs-action feedback
Feedback	The full database/archive	All feedback: new, planned, shipped, closed, duplicates, spam, etc.
So:
Inbox = things that need review
Feedback = everything ever submitted
Example
Imagine you have 500 total feedback items.
Section	Contains
Inbox	23 new/unreviewed items
Feedback	All 500 items, including closed, shipped, duplicate, spam, archived
The Inbox is a workflow page.
The Feedback page is a database/search page.
-	Regarding D6, go with what you recommended but take into account what I gave you for D5
-	Regarding D7, make sure to take into account what I gave you regarding D5
-	Regarding D9, Definitely want a page that is more of like a landing/marketing page instead of just throwing users into the login screen or app. This not only sells the app, but also provides clarity to users what this app even is.I feel like it would be nice to have a mini demo in this page of what the app can do and anyone can try the demo out to see if they like some functionality of the app.
-	Regarding D10, use actual tailwind unless you have a good reason not too. Regarding conventions about how css and styling will work, I think I will differ to notes/frontend-conventions.md
-	Regarding D16, I think I can handle creating the favicon, generate a placeholder for now, and we can put your recommendation as a backup in case I don’t up succeeding with the favicon.
-	To be clear we’re combining all versions into one sprint v2, v3, etc…
-	Everything else, go with what you recommended

Let me know if you have pushback on this
