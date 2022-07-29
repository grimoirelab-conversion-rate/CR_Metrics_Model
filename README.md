# Conversion Rate Metrics Model

The Experimental Conversion Rate Metrics Model (WIP &amp; Unofficial). This project is mostly learned from the Activity Metrics Model[^1]. And this repo would be part of [@TieWay59](https://github.com/TieWay59)'s GSoC 2020 deliverables.

## How To Use

### Dev Setup

1. Choose the `python = "^3.7"` interpreter for a virtual environment.
2. Fork & Clone sirmordred[^2] and follow its tutorial[^3].
   - I believe there is no need to clone all related grimoirelab projects anymore, just skip that and go to the next step.
3. Install poetry and run `poetry install`.
   - It will install every grimoirelab python module from GitHub and also include the SirMordred itself.
4. Follow grimoirelab-gitee/grimoirelab tutorial[^4] for the gitee data support.
   - The old codebase might contain the missing `__init__.py` error, you might need to delete some `perceval/__init__.py` or `perceval/backends/__init__.py` according to the referred issue discussion[^5].
5. Make sure you have your `projects.json` and have collected enough data for you as your wish.
6. Create `config.yml` flowing patterns blow (see [`config.yml`](./config.yaml) in this repo):

   - I use the `gitee_issues-raw` from the Gitee data source as my `issue_index` for the test.
   - This config file is designed for the Activity Metrics Model[^1] and the Conversion Rate Metrics Model is still in progress.

   ```yaml
   url: "https://username:password@localhost:9200"
   params:
     issue_index: # Issue index
     json_file: # json file for repos messages
     git_index: # git index
     git_branch: # None, leave it empty
     from_date: # (default "1970-01-01") the beginning of time for metric model
     end_date: # (default today) the end of time for metric model
     out_index: # new index for metric model
     community: # the name of community
     level: # representation of the metrics, choose from repo, project or community.
   ```

7. Create a `projects.json` file, and it's the same as the `projects.json` concept in grimoirelab. Since the script will use the repo URL to filter data, so please keep in mind that you should have collected the data before this process.
8. Run `python cr_metric_model.py` and if it works, you'll find the `out_index` in the Kibiter index patterns.

<!-- TODO -->

[^1]: [grimoirelab-gitee/metrics_model(github.com)](https://github.com/grimoirelab-gitee/metrics_model)
[^2]: [grimoirelab-sirmordred/Getting-Started.md at master - chaoss/grimoirelab-sirmordred (github.com)](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/Getting-Started.md)
[^3]: [grimoirelab-sirmordred/Getting-Started.md at master · chaoss/grimoirelab-sirmordred](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/Getting-Started.md)
[^4]: [How to run grimoirelab gitee? - grimoirelab-gitee/grimoirelab Wiki (github.com)](https://github.com/grimoirelab-gitee/grimoirelab/wiki/How-to-run-grimoirelab-gitee%3F)
[^5]: [Release 0.19.1 missing **init**.py (package not found error) - Issue #791 - chaoss/grimoirelab-perceval (github.com)](https://github.com/chaoss/grimoirelab-perceval/issues/791)
