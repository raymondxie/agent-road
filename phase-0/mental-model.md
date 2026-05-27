# Agent Engineering Mental Model

*Written from memory after reading Phase 0 resources. No copy-paste.*

---

## 1. Workflow vs. Agent

<!-- What is the core distinction? When would you choose one over the other? -->
Workflow follows a pre-defined steps, while agent makes decision dynamically to move forward.
Workflow provides predictability for cases of well defined process; Agent gives the flexibility for scenarios where the task steps are not well known or fixed before hand.

## 2. Augmented LLM

<!-- What does "augmented" mean here? What are the three augmentations? -->
Enhancements around LLM models to make it more effective.
1. Retrieval;
2. Tool;
3. Memory;

## 3. The Four Context-Engineering Primitives

### Write
<!-- What is it? Give a concrete example. -->
Agent actively writes information to persistent storage.
In CC for example, writing PLAN.md, NOTES.md to file system, to be used in long horizon tasks.

### Select
<!-- What is it? Give a concrete example. -->
In order to effectively utilizing context and avoiding context rot, we shall select the smallest set of context information that conveys our expected behavior, that is most relevant to that step.
For example, just-in-time context by augumenting retrieval to pull in things that only necessary and important to that step.

### Compress
<!-- When does this trigger? What's the threshold? -->
When context size is approaching to the context window of LLM, it triggers compaction.
The compaction effectively reduce the size of context with summarization and other technique but preserve all or most relevant context information.

### Isolate
<!-- Why does this matter? What problem does it solve? -->
Keep context informative yet tight. It prevents context pollution and performance degradation.
In sub-agent scenarios, each sub-agent can have large context for deep work towards one area, without affecting orchestrator context window limitation and behavior.

## 4. Orchestrator-Worker Pattern

<!-- Describe the pattern. What does the orchestrator do vs. the worker? -->
One agent is in charge of managing complex tasks, and coordinating and delegating tasks to worker agent for specific works, and then aggregating results from work agents to determine the next iteration.
Orchestrator manages the overall planning, task breakdowns, delegation, and coordination; while worker agents carry out task and report back results.

## 5. Harness vs. Model vs. Framework

<!-- What is each layer responsible for? Why does the harness matter more than model choice? -->
Agent = Model + Harness.
Model is the intelligence, and Harness is everything else around model that make it more effective in accomplishing real-world tasks. Framework is a pre-defined set of components / processes that embody common patterns and best practices.
As models are saturating and converging, there is no significant difference in raw intelligence. But how harness is constructed and organized can lead to very different outcomes, and so at the moment, harness engineering is an important and active research area.

## 6. Top Three Failure Modes

<!-- The most common ways agents fail in production. -->
1. bloated tools
2. system prompt too specific
3. system prompt too vague

For AI review, based on trained knowledge, which I think is reasonable but they are not appeared in the 3 articles I read. 
1. irreversible actions
2. cascading errors
3. insufficient verification checkpoints

## 7. The 15× Token Trade-off

<!-- When is multi-agent worth the 15× token overhead? When is it not? -->
If the scenario can be broken down into independent threads requiring deep work and large context, the parallelization gain and context isolation may warrant the 15× token overhead. 
Otherwise, a simple ReAct loop may do a better job.

Reason: parallelization, context isolation

---

*Completed: May 27, 2026
