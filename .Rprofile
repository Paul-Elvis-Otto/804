source("renv/activate.R")
# enable pak for renv
options(renv.config.pak.enabled = TRUE)

# if not available install pak
if (!requireNamespace("pak", quietly = TRUE)) {
    # this writes pak into your renv library and lockfile
    renv::install("pak")
  }

if (!requireNamespace("languageserver", quietly = TRUE)) {
    # this writes remotes into your renv library and lockfile
    renv::install("languageserver")
  }
