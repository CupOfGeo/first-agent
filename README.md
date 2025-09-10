# My First Agent
I wanted to build an actual useful agent i can deploy and automate away a once manual task.

Problem: My friend has to go to this website calendar everyday and check if has been updated and make sure his google calendar is in sync with it.

Solution: AI agent that gets the data and keeps a google cal in sync so that he doesn't have to.

Here are some of the best practices I tried to implement in an ai agent

# Getting starter
you'll need to make an anthropic api key https://console.anthropic.com/settings/keys
then save it to your .env `ANTHROPIC_API_KEY=sk-ant-api.....`


## Design Patterns
I believe in "All user input is an error" and it's the same if not more for llm's. I want to restrict there environment of action as much as possible in order to minimize error and cost.

### Security - TODO
removed for now bc of complexity issues
So the agent only has access to run the one shell script. It passes in an env variable set by me. So the attack surface of prompt injection still comes in from the calendar but at that point an attacker already hacked a government court website. (todo check with my attorney if im liable XD).

The application uses a multi-layered security approach with Docker containerization and SELinux policies. The Dockerfile creates a restricted user environment where the agent runs with minimal privileges. Additionally, SELinux type enforcement policies provide mandatory access controls, restricting the agent to only interact with specific files and execute pre-defined scripts. This defense-in-depth strategy ensures that even if the LLM is compromised through prompt injection, the damage is contained within strict security boundaries.

### Auditing and prompt testing
I need a way to test prompts and failures.
I saw the output of the curl request and the starting calendar state and pass the files to the agent. This way if/when it fails I can easily replay the exact prompt that was given. The future state this can be a database.

### Alerting User
also for auditing purposes is send a text of todays meeting. I do this as a sort of shadow AI I cant have my ai be silently failing and him not being updated. So for now it also texts him until he wants me to turn that off.
