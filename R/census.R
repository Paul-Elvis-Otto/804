library(tidycensus)
library(tidyverse)
library(cluster)

# Set Census API key (get yours at https://api.census.gov/data/key_signup.html)
# census_api_key("your_key_here", install = TRUE)

# Configuration
year <- 2023
survey <- "acs5"

# This is the Var list of the api
# https://api.census.gov/data/2019/acs/acs5/variables.html
#
# ACS Variables with descriptions
# Economics:
#   B19013_001 - Median household income in the past 12 months
#   B17001_001 - Poverty status in the past 12 months (total)
#   B17001_002 - Income in the past 12 months below poverty level
#   B19083_001 - Gini index of income inequality
# Education (age 25+):
#   B15003_001 - Total population 25+ years
#   B15003_021 - Bachelor's degree
#   B15003_022 - Master's degree
#   B15003_023 - Professional school degree
#   B15003_025 - Doctorate degree
# Labor force:
#   B23025_001 - Population 16+ years
#   B23025_003 - Civilian labor force
#   B23025_004 - Employed
#   B23025_005 - Unemployed
# Demographics:
#   B01002_001 - Median age
#   B01003_001 - Total population
#   B02001_001 - Total race population
#   B02001_003 - Black or African American alone
#   B03003_001 - Total Hispanic origin population
#   B03003_003 - Hispanic or Latino
#   B05002_001 - Total place of birth population
#   B05002_013 - Foreign born
vars <- c(
  med_income = "B19013_001",
  pov_total = "B17001_001",
  pov_below = "B17001_002",
  gini = "B19083_001",
  edu_total = "B15003_001",
  ba = "B15003_021",
  ma = "B15003_022",
  prof = "B15003_023",
  phd = "B15003_025",
  pop16 = "B23025_001",
  labor_force = "B23025_003",
  employed = "B23025_004",
  unemployed = "B23025_005",
  median_age = "B01002_001",
  pop_total = "B01003_001",
  race_total = "B02001_001",
  black = "B02001_003",
  hisp_total = "B03003_001",
  hisp = "B03003_003",
  fb_total = "B05002_001",
  foreign_born = "B05002_013"
)

# Fetch ACS data for all states
acs_raw <- get_acs(
  geography = "state",
  variables = vars,
  year = year,
  survey = survey,
  output = "wide"
)

# Process and calculate derived variables
acs <- acs_raw |>
  transmute(
    state = NAME,

    # Economics
    med_income = med_incomeE,
    poverty_rate = pov_belowE / pov_totalE,
    gini = giniE,

    # Education: Bachelor's degree or higher
    ba_plus = (baE + maE + profE + phdE) / edu_totalE,

    # Labor market
    unemployment_rate = unemployedE / labor_forceE,
    lfpr = labor_forceE / pop16E,
    employment_pop_ratio = employedE / pop16E,

    # Demographics
    median_age = median_ageE,
    pct_black = blackE / race_totalE,
    pct_hispanic = hispE / hisp_totalE,
    pct_foreign_born = foreign_bornE / fb_totalE,
    population = pop_totalE
  )

# Calculate closest states using standardized Euclidean distance
closest_states <- function(data, features, target = "North Carolina", n = 5) {
  df <- data |>
    select(state, all_of(features)) |>
    drop_na()

  X <- scale(df |> select(-state))
  target_row <- which(df$state == target)
  target_vec <- X[target_row, ]

  distances <- sqrt(rowSums((X - target_vec)^2))

  df |>
    mutate(distance = distances) |>
    filter(state != target) |>
    arrange(distance) |>
    slice_head(n = n)
}

# Define feature groups
economics_vars <- c("med_income", "poverty_rate", "gini")
education_vars <- c("ba_plus")
labor_vars <- c("unemployment_rate", "lfpr", "employment_pop_ratio")
demographics_vars <- c(
  "median_age",
  "pct_black",
  "pct_hispanic",
  "pct_foreign_born",
  "population"
)

# Calculate similarities for each domain
cat("\n=== Economics ===\n")
closest_states(acs, economics_vars)

cat("\n=== Education ===\n")
closest_states(acs, education_vars)

cat("\n=== Labor Market ===\n")
closest_states(acs, labor_vars)

cat("\n=== Demographics ===\n")
closest_states(acs, demographics_vars)

cat("\n=== All Variables ===\n")
all_vars <- c(economics_vars, education_vars, labor_vars, demographics_vars)
closest_states(acs, all_vars)
