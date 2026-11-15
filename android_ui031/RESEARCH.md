# UI research and decisions — 2026-11-15

Sources consulted: the public ChatGPT home page, OpenAI's search help page and
its composer/source images; Claude's official web-search and model/thinking
documentation. Direct claude.ai access was restricted, so this is not a claim
to have navigated an authenticated Claude session. UI details vary by rollout.

- https://chatgpt.com/
- https://help.openai.com/en/articles/9237897-searching-the-web-with-chatgpt
- https://support.claude.com/en/articles/10684626-enable-and-use-web-search
- https://support.claude.com/en/articles/8664678-change-the-model-effort-and-thinking-settings

The previous Android UI had several large persistent buttons and equal-looking
cards for user, assistant and tool messages. Model/profile controls competed
with the conversation. Tool output was a large plaintext block; only one current
conversation per profile was visible, and thinking was a changing placeholder.

The new design borrows interaction patterns: compact top model picker, navigation
drawer, centered reading column, neutral user bubble, flowing assistant answer,
rounded composer, restrained typography and collapsible activity/source panels.
It uses Liquid Sense's own branding and a charcoal/lavender palette with a serif
welcome heading. No OpenAI/Anthropic logos, accounts or APIs are added.

Base and Base-offline are explicitly the same weights with different tools.
Experimental029epoch02 and Code015E are grouped separately, with limitations and
installation status. All four legacy IDs and reasoning presets remain intact.

Activity is driven by actual engine callbacks and tool execution. A generated
partial tool call only means preparing, not searching. Search/Python states start
inside validated execution. Source cards show returned observations. Thought
details contain only the small model's actual raw output, with forced closures
labelled. Animation is an activity indicator, not a fabricated progress estimate.

## Languages and Goose

The app was already mixed-language: Rust inference through JNI, Java Android UI
and agent orchestration, MicroPython's C executor.031 adds HTML/CSS/JavaScript
for the locally bundled presentation; Java still owns model/tool execution.

The requested Goose appears to be Aardappel/Wouter van Oortmerssen's language:
https://aardappel.github.io/goose/ . Its own documentation describes a new
whole-program compiler that emits C, inline/data-stack storage and a small
standard library. Its published speed numbers concern its own benchmark suite;
they do not measure this model's matrix kernels, Android integration or UI.
No benefit was established for adding it here, so031 adds no Goose dependency
and makes no inference speed claim. A separate bounded benchmark of a relevant
kernel would be necessary before considering a runtime migration.

## Validation limits

The production HTML/CSS/JS was tested in Chromium with a mocked Java bridge,
including mobile/desktop layouts and a locally intercepted HTTPS asset origin.
Mock responses are only test fixtures, never APK answers or evidence of model
quality. Android resources/Java/DEX, package, signature, alignment and asset
digests are checked separately. No Android phone/emulator execution is claimed.

Legacy030weights and both native libraries remain byte-identical, with no new
training. The known Rust/Python generation mismatch and quality regressions
remain. This release changes presentation and local history management.
