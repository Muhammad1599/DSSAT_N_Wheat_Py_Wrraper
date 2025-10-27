# Install required packages for lte_duernast_data_mapping.R to user library
cat("Installing required R packages to user library...\n")

# Create user library if it doesn't exist
user_lib <- Sys.getenv("R_LIBS_USER")
if (!dir.exists(user_lib)) {
  dir.create(user_lib, recursive = TRUE, showWarnings = FALSE)
  cat(paste("Created user library at:", user_lib, "\n"))
}

# Add user library to library path
.libPaths(c(user_lib, .libPaths()))

cat(paste("Installing to:", user_lib, "\n\n"))

# Check and install CRAN packages
required_packages <- c("devtools", "dplyr", "openxlsx2", "sf")

for (pkg in required_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(paste("Installing", pkg, "...\n"))
    tryCatch({
      install.packages(pkg, lib = user_lib, repos = "https://cloud.r-project.org/", 
                       dependencies = TRUE, type = "binary")
      cat(paste(pkg, "installed successfully\n\n"))
    }, error = function(e) {
      cat(paste("Error installing", pkg, ":", e$message, "\n"))
    })
  } else {
    cat(paste(pkg, "is already installed\n"))
  }
}

cat("\n=== Installation Summary ===\n")
cat("Library paths:\n")
print(.libPaths())
cat("\nInstalled packages:\n")
print(installed.packages(lib.loc = user_lib)[, c("Package", "Version")])
