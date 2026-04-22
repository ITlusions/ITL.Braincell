# BrainCell MCP — Quick Reference

Server: `http://localhost:9506/mcp`

---

## Cross-cell tools

| Tool                   | Args                                    | Returns                          |
|------------------------|-----------------------------------------|----------------------------------|
| `search_memory`        | `query, memory_type?, limit=10`         | Decisions + snippets + arch notes |
| `get_relevant_context` | `query, limit=5`                        | Semantic results + recent decisions |

---

## Per-cell tools

### Interactions (primary write path — triggers auto-detection)
| Tool                   | Key args                                         |
|------------------------|--------------------------------------------------|
| `interactions_save`    | `content, role, conversation_id?, session_id?`  |
| `interactions_search`  | `query, limit=10`                               |
| `interactions_list`    | `limit=50`                                      |

### Conversations
| Tool                   | Key args                  |
|------------------------|---------------------------|
| `conversations_save`   | `session_name, summary?`  |
| `conversations_search` | `query, limit=10`         |
| `conversations_list`   | `limit=50`                |

### Sessions
| Tool              | Key args                         |
|-------------------|----------------------------------|
| `sessions_save`   | `session_name, status?, summary?`|
| `sessions_search` | `query, limit=10`               |
| `sessions_list`   | `limit=50`                       |

### Decisions
| Tool               | Key args                                    |
|--------------------|---------------------------------------------|
| `decisions_save`   | `decision, rationale?, impact?, status?`    |
| `decisions_search` | `query, limit=10`                           |
| `decisions_list`   | `limit=50`                                  |

### Architecture Notes
| Tool                        | Key args                            |
|-----------------------------|-------------------------------------|
| `architecture_notes_save`   | `component, description, tags?`     |
| `architecture_notes_search` | `query, limit=10`                   |
| `architecture_notes_list`   | `limit=50`                          |

### Snippets
| Tool              | Key args                                          |
|-------------------|---------------------------------------------------|
| `snippets_save`   | `title, code_content, language?, description?`    |
| `snippets_search` | `query, limit=10`                                 |
| `snippets_list`   | `limit=50`                                        |

### Files Discussed
| Tool                     | Key args                             |
|--------------------------|--------------------------------------|
| `files_discussed_save`   | `file_path, language?, description?` |
| `files_discussed_search` | `query, limit=10`                    |
| `files_discussed_list`   | `limit=50`                           |

### Notes
| Tool           | Key args                              |
|----------------|---------------------------------------|
| `notes_save`   | `title, content, tags?, source?`      |
| `notes_search` | `query, limit=10`                     |
| `notes_list`   | `limit=50`                            |

### Research Questions
| Tool              | Key args                                    |
|-------------------|---------------------------------------------|
| `question_save`   | `question, status?, priority?, context?`    |
| `question_search` | `query, status?, limit=10`                  |
| `question_list`   | `status?, limit=50`                         |

### Tasks
| Tool           | Key args                                               |
|----------------|--------------------------------------------------------|
| `tasks_save`   | `title, description?, status?, priority?, project?`   |
| `tasks_search` | `query, limit=20`                                     |
| `tasks_list`   | `status?, project?, priority?, limit=50`              |

### Incidents
| Tool               | Key args                                         |
|--------------------|--------------------------------------------------|
| `incidents_save`   | `title, severity?, status?, description?`        |
| `incidents_search` | `query, limit=10`                               |

### IOCs
| Tool         | Key args                                               |
|--------------|--------------------------------------------------------|
| `ioc_save`   | `value, type?*, confidence?, severity?, source?`      |
| `ioc_search` | `query, ioc_type?, limit=20`                          |

*`type` auto-detected from `value` pattern (IP, hash, CVE, domain, etc.)

### Threats (Threat Actors)
| Tool              | Key args                                   |
|-------------------|--------------------------------------------|
| `threats_save`    | `name, classification?, ttps?, status?`    |
| `threats_search`  | `query, limit=10`                          |

### Intel Reports
| Tool                   | Key args                                          |
|------------------------|---------------------------------------------------|
| `intel_reports_save`   | `title, summary?, content?, tlp_level?, analyst?` |
| `intel_reports_search` | `query, limit=10`                                |

### Vuln Patches
| Tool                  | Key args                                                       |
|-----------------------|----------------------------------------------------------------|
| `vuln_patches_save`   | `title, vulnerable_code, patched_code, language?, severity?`  |
| `vuln_patches_search` | `query, language?, limit=10`                                  |

### Runbooks
| Tool               | Key args                                   |
|--------------------|--------------------------------------------|
| `runbooks_save`    | `title, steps, category?, trigger?`        |
| `runbooks_search`  | `query, category?, limit=10`              |
| `runbooks_get`     | `runbook_id`                               |

### Dependencies
| Tool                  | Key args                                          |
|-----------------------|---------------------------------------------------|
| `dependencies_save`   | `name, version, ecosystem?, status?, cve_refs?`   |
| `dependencies_search` | `query, ecosystem?, status?, limit=10`            |

### API Contracts
| Tool                       | Key args                                    |
|----------------------------|---------------------------------------------|
| `api_contracts_save`       | `title, service_name, version, status?`     |
| `api_contracts_search`     | `query, limit=10`                           |
| `api_contracts_list_services` | `limit=50`                              |

---

## Status enums cheat sheet

| Field         | Values                                              |
|---------------|-----------------------------------------------------|
| task status   | `open` `in_progress` `blocked` `done` `cancelled`  |
| task priority | `critical` `high` `medium` `low`                   |
| ioc type      | `ip` `domain` `hash_md5` `hash_sha1` `hash_sha256` `url` `email` `cve` `yara` |
| ioc status    | `active` `expired` `false_positive` `under_review` |
| tlp_level     | `WHITE` `GREEN` `AMBER` `RED`                       |
| incident status | `open` `investigating` `contained` `resolved` `closed` |
| question status | `pending` `investigating` `answered` `closed`    |
