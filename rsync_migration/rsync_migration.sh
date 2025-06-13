#!/bin/bash

# Interactive Rsync Migration Script
# Safely sync data between MacBooks with integrity checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to validate paths
validate_path() {
    local path="$1"
    local type="$2"
    
    if [[ "$path" =~ ^[a-zA-Z0-9@._-]+: ]]; then
        # Remote path - basic validation
        if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${path%%:*}" "test -d '${path#*:}'" 2>/dev/null; then
            print_error "Cannot access remote path: $path"
            return 1
        fi
    else
        # Local path
        if [ "$type" = "source" ]; then
            if [ ! -d "$path" ]; then
                print_error "Source directory does not exist: $path"
                return 1
            fi
        else
            # For destination, create parent directory if it doesn't exist
            local parent_dir=$(dirname "$path")
            if [ ! -d "$parent_dir" ]; then
                print_warning "Parent directory doesn't exist, creating: $parent_dir"
                mkdir -p "$parent_dir" || return 1
            fi
        fi
    fi
    return 0
}

# Function to estimate transfer size
estimate_size() {
    local source="$1"
    print_status "Estimating transfer size..."
    
    if [[ "$source" =~ ^[a-zA-Z0-9@._-]+: ]]; then
        # Remote source
        ssh "${source%%:*}" "du -sh '${source#*:}'" 2>/dev/null || echo "Size estimation failed"
    else
        # Local source
        du -sh "$source" 2>/dev/null || echo "Size estimation failed"
    fi
}

# Function to create exclusion patterns
create_exclusions() {
    local exclude_file="/tmp/rsync_exclude_$$"
    
    cat > "$exclude_file" << 'EOF'
# System files and folders
.DS_Store
.Spotlight-V100
.Trashes
.fseventsd
.TemporaryItems
.DocumentRevisions-V100
.PKInstallSandboxManager
.PKInstallSandboxManager-SystemSoftware

# System directories
/System/
/Library/System/
/usr/
/var/
/tmp/
/private/
/dev/
/Applications/
/Library/Application Support/
/Library/Caches/
/Library/LaunchAgents/
/Library/LaunchDaemons/
/Library/Logs/
/Library/Preferences/

# User cache and temp files
**/.cache/
**/Cache/
**/Caches/
**/*cache*
**/*.tmp
**/*.temp
**/Trash/

# Version control
**/.git/
**/.svn/
**/.hg/

# Virtual environments and dependencies
**/node_modules/
**/venv/
**/env/
**/__pycache__/

# Large files that might not be needed
*.iso
*.dmg
*.ova
*.vmdk
*.vdi

# Swap files
**/.swp
**/*.swp
EOF

    echo "$exclude_file"
}

# Function to perform dry run
dry_run() {
    local source="$1"
    local destination="$2"
    local exclude_file="$3"
    
    print_status "Performing dry run to check what will be transferred..."
    echo ""
    
    rsync -avhn --progress --stats \
        --exclude-from="$exclude_file" \
        --itemize-changes \
        "$source" "$destination" | head -50
    
    echo ""
    print_warning "This is a DRY RUN - no files were actually transferred."
    echo ""
}

# Function to perform actual sync
perform_sync() {
    local source="$1"
    local destination="$2"
    local exclude_file="$3"
    
    print_status "Starting file synchronization..."
    print_status "Press Ctrl+C to cancel if needed"
    echo ""
    
    # Add checksum verification for critical files
    rsync -avh --progress --stats \
        --exclude-from="$exclude_file" \
        --checksum \
        --partial \
        --partial-dir=.rsync-partial \
        "$source" "$destination"
}

# Function to verify integrity
verify_integrity() {
    local source="$1"
    local destination="$2"
    
    print_status "Performing post-sync verification..."
    
    # Count files
    if [[ "$source" =~ ^[a-zA-Z0-9@._-]+: ]]; then
        source_count=$(ssh "${source%%:*}" "find '${source#*:}' -type f | wc -l" 2>/dev/null || echo "0")
    else
        source_count=$(find "$source" -type f | wc -l 2>/dev/null || echo "0")
    fi
    
    if [[ "$destination" =~ ^[a-zA-Z0-9@._-]+: ]]; then
        dest_count=$(ssh "${destination%%:*}" "find '${destination#*:}' -type f | wc -l" 2>/dev/null || echo "0")
    else
        dest_count=$(find "$destination" -type f | wc -l 2>/dev/null || echo "0")
    fi
    
    echo "Source files: $source_count"
    echo "Destination files: $dest_count"
    
    if [ "$source_count" -eq "$dest_count" ] && [ "$source_count" -gt 0 ]; then
        print_success "File count verification passed!"
    else
        print_warning "File counts don't match - this might be normal due to exclusions"
    fi
}

# Main script
main() {
    echo "======================================"
    echo "  Interactive Rsync Migration Tool"
    echo "======================================"
    echo ""
    
    # Get source path
    while true; do
        echo "Enter source path:"
        echo "  Local: /Users/username/Documents"
        echo "  Remote: user@hostname:/path/to/source"
        read -p "Source: " source_path
        
        if [ -z "$source_path" ]; then
            print_error "Source path cannot be empty"
            continue
        fi
        
        if validate_path "$source_path" "source"; then
            break
        fi
    done
    
    # Get destination path
    while true; do
        echo ""
        echo "Enter destination path:"
        echo "  Local: /Users/username/Documents"
        echo "  Remote: user@hostname:/path/to/destination"
        read -p "Destination: " dest_path
        
        if [ -z "$dest_path" ]; then
            print_error "Destination path cannot be empty"
            continue
        fi
        
        if validate_path "$dest_path" "destination"; then
            break
        fi
    done
    
    # Ensure source ends with / for proper rsync behavior
    if [[ "$source_path" != */ ]]; then
        source_path="$source_path/"
    fi
    
    echo ""
    print_status "Configuration:"
    echo "  Source: $source_path"
    echo "  Destination: $dest_path"
    echo ""
    
    # Estimate size
    estimate_size "$source_path"
    echo ""
    
    # Create exclusion file
    exclude_file=$(create_exclusions)
    print_status "Created exclusion patterns for system files"
    
    # Ask for dry run
    read -p "Perform dry run first? (recommended) [Y/n]: " do_dry_run
    if [[ "$do_dry_run" != "n" && "$do_dry_run" != "N" ]]; then
        dry_run "$source_path" "$dest_path" "$exclude_file"
        
        read -p "Continue with actual sync? [Y/n]: " continue_sync
        if [[ "$continue_sync" == "n" || "$continue_sync" == "N" ]]; then
            print_status "Sync cancelled by user"
            cleanup "$exclude_file"
            exit 0
        fi
    fi
    
    # Perform the sync
    echo ""
    read -p "Ready to start sync. Continue? [Y/n]: " final_confirm
    if [[ "$final_confirm" == "n" || "$final_confirm" == "N" ]]; then
        print_status "Sync cancelled by user"
        cleanup "$exclude_file"
        exit 0
    fi
    
    # Record start time
    start_time=$(date)
    print_status "Sync started at: $start_time"
    
    # Perform sync
    if perform_sync "$source_path" "$dest_path" "$exclude_file"; then
        print_success "Sync completed successfully!"
        
        # Verify integrity
        verify_integrity "$source_path" "$dest_path"
        
        end_time=$(date)
        print_success "Migration completed at: $end_time"
    else
        print_error "Sync failed!"
        cleanup "$exclude_file"
        exit 1
    fi
    
    # Cleanup
    cleanup "$exclude_file"
}

# Cleanup function
cleanup() {
    local exclude_file="$1"
    if [ -f "$exclude_file" ]; then
        rm "$exclude_file"
    fi
}

# Trap to cleanup on exit
trap 'cleanup "/tmp/rsync_exclude_$$"' EXIT

# Run main function
main "$@"