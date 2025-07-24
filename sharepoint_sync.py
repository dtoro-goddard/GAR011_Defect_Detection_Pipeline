"""
SharePoint Sync Module

Handles authentication and bi-directional sync between a local folder and a SharePoint folder.
"""

from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.files.file import File
from datetime import datetime
import os
from pathlib import Path
import logging

class SharePointSync:
    def __init__(self, site_url, sharepoint_folder, local_folder, direction="both", client_id=None, client_secret=None, username=None, password=None):
        """
        Initialize SharePointSync.
        Args:
            site_url: SharePoint site URL
            sharepoint_folder: Document library/folder (e.g. 'Shared Documents/Folder')
            local_folder: Local folder to sync
            direction: 'to-local', 'to-sharepoint', or 'both'
            client_id: Azure AD App client ID (optional)
            client_secret: Azure AD App client secret (optional)
            username: SharePoint username (optional)
            password: SharePoint password (optional)
        """
        self.site_url = site_url
        self.sharepoint_folder = sharepoint_folder
        self.local_folder = local_folder
        self.direction = direction
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.ctx = None
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("SharePointSync")

    def authenticate(self):
        """
        Authenticate to SharePoint using provided credentials.
        Supports both username/password and Azure AD App credentials.
        Sets self.ctx to an authenticated ClientContext.
        Raises Exception on failure.
        """
        if self.client_id and self.client_secret:
            # Azure AD App-Only authentication
            try:
                creds = ClientCredential(self.client_id, self.client_secret)
                self.ctx = ClientContext(self.site_url).with_credentials(creds)
                self.ctx.web.get().execute_query()
                return self.ctx
            except Exception as e:
                raise Exception(f"SharePoint Azure AD App authentication failed: {e}")
        elif self.username and self.password:
            # Username/password authentication
            try:
                creds = UserCredential(self.username, self.password)
                self.ctx = ClientContext(self.site_url).with_credentials(creds)
                self.ctx.web.get().execute_query()
                return self.ctx
            except Exception as e:
                raise Exception(f"SharePoint username/password authentication failed: {e}")
        else:
            raise Exception("No valid SharePoint credentials provided. Provide either client_id/client_secret or username/password.")

    def sync(self):
        """
        Perform sync between local and SharePoint folders.
        Supports 'to-local', 'to-sharepoint', and 'both' directions.
        Recursively compares files/folders by name and last-modified time.
        Only transfers new or changed files. Logs actions and errors.
        """
        if not self.ctx:
            self.authenticate()
        self.logger.info(f"Starting sync: {self.direction}")
        sharepoint_root = self.sharepoint_folder
        local_root = Path(self.local_folder)
        local_root.mkdir(parents=True, exist_ok=True)
        if self.direction in ("to-local", "both"):
            self.logger.info("Syncing SharePoint -> Local...")
            self._sync_sharepoint_to_local(sharepoint_root, local_root)
        if self.direction in ("to-sharepoint", "both"):
            self.logger.info("Syncing Local -> SharePoint...")
            self._sync_local_to_sharepoint(local_root, sharepoint_root)
        self.logger.info("Sync complete.")

    def _sync_sharepoint_to_local(self, sp_folder_url, local_folder):
        """
        Recursively download new/changed files from SharePoint to local folder.
        """
        try:
            folder = self.ctx.web.get_folder_by_server_relative_url(sp_folder_url)
            files = folder.files
            self.ctx.load(files)
            self.ctx.execute_query()
            for file in files:
                local_file = local_folder / file.properties['Name']
                sp_time = datetime.strptime(file.properties['TimeLastModified'], "%Y-%m-%dT%H:%M:%SZ")
                if local_file.exists():
                    local_time = datetime.fromtimestamp(local_file.stat().st_mtime)
                    if abs((local_time - sp_time).total_seconds()) < 2:
                        self.logger.info(f"Up-to-date: {local_file}")
                        continue
                self.logger.info(f"Downloading: {file.properties['ServerRelativeUrl']} -> {local_file}")
                response = File.open_binary(self.ctx, file.properties['ServerRelativeUrl'])
                with open(local_file, "wb") as f:
                    f.write(response.content)
                os.utime(local_file, (sp_time.timestamp(), sp_time.timestamp()))
            # Recurse into subfolders
            folders = folder.folders
            self.ctx.load(folders)
            self.ctx.execute_query()
            for subfolder in folders:
                if subfolder.properties['Name'] in ("Forms",):
                    continue
                self._sync_sharepoint_to_local(subfolder.properties['ServerRelativeUrl'], local_folder / subfolder.properties['Name'])
        except Exception as e:
            self.logger.error(f"Error syncing SharePoint to local: {e}")

    def _sync_local_to_sharepoint(self, local_folder, sp_folder_url):
        """
        Recursively upload new/changed files from local folder to SharePoint.
        """
        try:
            folder = self.ctx.web.get_folder_by_server_relative_url(sp_folder_url)
            self.ctx.load(folder)
            self.ctx.execute_query()
            # Get SharePoint files and folders
            sp_files = {f.properties['Name']: f for f in folder.files}
            self.ctx.load(folder.files)
            self.ctx.execute_query()
            sp_folders = {f.properties['Name']: f for f in folder.folders}
            self.ctx.load(folder.folders)
            self.ctx.execute_query()
            # Upload files
            for item in local_folder.iterdir():
                if item.is_file():
                    sp_file = sp_files.get(item.name)
                    local_time = datetime.fromtimestamp(item.stat().st_mtime)
                    upload = False
                    if sp_file:
                        sp_time = datetime.strptime(sp_file.properties['TimeLastModified'], "%Y-%m-%dT%H:%M:%SZ")
                        if (local_time - sp_time).total_seconds() > 2:
                            upload = True
                    else:
                        upload = True
                    if upload:
                        self.logger.info(f"Uploading: {item} -> {sp_folder_url}/{item.name}")
                        with open(item, "rb") as f:
                            folder.upload_file(item.name, f.read())
                        # Set modified time (not always possible)
                elif item.is_dir():
                    if item.name not in sp_folders:
                        self.logger.info(f"Creating folder in SharePoint: {sp_folder_url}/{item.name}")
                        folder.folders.add(item.name)
                        self.ctx.execute_query()
                    self._sync_local_to_sharepoint(item, f"{sp_folder_url}/{item.name}")
        except Exception as e:
            self.logger.error(f"Error syncing local to SharePoint: {e}") 