/**
 * Changelog release data for the single-version changelog viewer.
 * Newest releases first.
 */
const CHANGELOG = [
  {
    version: "v2.16.1",
    date: "August 8, 2026",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Visually redesign all pages to be less Fomantic UI-specific",
            children: [
              { html: "Rewrite how season titles are entered" },
              { html: "On the Series and Templates pages, the visible extras for a specific card type are now swapped via a dropdown, rather than 20+ tabs" },
            ],
          },
          { html: "Display a message in the UI to indicate you must restart TCM for changes to the Scheduler to take effect" },
          { html: "Make enabling Kanji translations much more user friendly by adding a simple Kanji checkbox" },
          {
            html: "Various performance improvements",
            children: [
              { html: "For example: only query Series images, logs, and Episode data when each respective tab is opened" },
              { html: "Add eager- and selectinload- query modifiers to the SQL query for loading Series Cards - this should be an approximate 2x speed improvement" },
              { html: "Significantly improve logging database performance by enabling WAL mode on the database connection (thanks @AnonFawkes for the suggestion)" },
              { html: `Add Source Images as an explicit SQL table within the database; rather than dynamically "finding" source image files in your file system whenever they're utilized` },
            ]
          },
          { html: "For Extras with explicitly defined allowable values - such as the Tinted Frame's Top Element extra allowing index, logo, omit, or title - display these options as dropdowns (not plain inputs) within the UI"},
          { html: "Begin distributing frontend HTML/CSS/JS files as part of the code base, rather than loading via CDN, to improve usability in offline environments" },
          { html: "Add ability to search for a Blueprint from any Series and import it while on the Series page - this can be used if you'd like to use a Blueprint on a Series it was not originally designed for" },
          { html: "Add command line functionality to create Posters (season, movie, and genre) - this brings the CLI to feature parity of V1" },
        ],
      },
      {
        title: "Major Fixes",
        items: [
          { html: "Fix package-specific logging interception - was incorrectly intercepting logging from all packages" },
          { html: "Handle timezone-unaware airdates from TMDb for episodes listed as movies" },
          { html: "Improve handling of Scheduler crontabs which start or end with spaces" },
          { html: "Improve the Series and Episode matching algorithms to improve handling of items with no metadata - these were previously always failing to match" },
        ],
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: `Add various new environment variables - you can read more about these <a href="https://titlecardmaker.com/user_guide/#environment-variables" target="_blank">here</a>`,
            children: [
              { html: "API connection timeout variables for each connection type (i.e. Emby, Jellyfin, etc.)" },
              { html: "ImageMagick command timeout" },
            ]
          },
          { html: "Add more verbose logging for non-JSON responses from various connections" },
          { html: "Create a helper script for viewing and querying user log databases" },
          { html: "Display a message if there are no Series logs, rather than just an empty page" },
          { html: "Log environment variables and huey task intervals on boot" },
          { html: "When performing many-to-many Episode matches, log a structured table of the match results to aid in debugging" },
          { html: "Add the style modal (from the Settings page) to the Series and Template pages" },
          { html: "Change the default database logging level to DEBUG (from TRACE) - this will reduce database sizes, but should be changed if needed for debugging" },
        ],
      },
      {
        title: "Minor Fixes",
        items: [
          { html: "Fix search-term highlighting for log messages which fit multiple style types" },
          { html: "Properly mark refresh buttons as loading on the logs page" },
          { html: "Fix typo on Series page tooltip" },
          { html: "Handle connection errors during CardType initialization which could have resulted in TCM failing to boot" },
          { html: "Fix the asset paths of various placeholder/web metadata files" },
        ],
      },
      {
        title: "Title Card Changes",
        items: [
          { html: "Add a builtin function <code>line_count</code> to get the number of lines in a piece of text - for example <code>{-20 if line_count(title_text) > 1 else 0}</code>"},
          {
            html: "All Card types",
            children: [
              { html: "Add command line interface functionality to all remaining card types" },
            ]
          },
          {
            html: "Banner",
            children: [
              { html: "Add the Episode Text Vertical Shift extra" }
            ]
          },
          {
            html: "Dictionary",
            children: [
              { html: "Change default word interword spacing from 100px to 75px, and scale it dynamically with the Word Size" },
            ]
          },
          {
            html: "Divider",
            children: [
              { html: "Fix divider height with partially hidden index text" },
            ]
          },
          {
            html: "Logo",
            children: [
              { html: "Add an Episode Text Font Size extra" },
              { html: "Fix incorrect centering of episode text (for very long index text)" },
            ]
          },
          {
            html: "Music",
            children: [
              { html: "Fix subtitle format string" },
            ]
          },
          {
            html: "Overline",
            children: [
              { html: "Fix episode text font - was incorrectly using the wrong font file" },
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          { html: "Write and finalize documentation for all remaining pages" },
          { html: "Add a note about changing branches to the Getting Started docs" },
          { html: "Remove animated header on website" },
          { html: "Update all Scheduler documentation to reflect changes to the basic/scheduler modes" },
          { html: "Add a note on how to remove the word text in the Dictionary card" },
          { html: "Fix the horizontal offset extra image for the Banner card" },
          { html: "Relocate the documentation on available Environment Variables - they're now located in the User Guide" },
          { html: `Document all command line image/card/poster creation <a href="https://titlecardmaker.com/user_guide/command_line/" target="_blank">here</a>` },
        ]
      },
      {
        title: "API Changes",
        items: [
          { html: "Remove all remaining deprecated API endpoints" },
        ]
      },
      {
        title: "Testing Changes",
        items: [
          { html: "Rewrite various tests to work with new frontend redesign" },
        ]
      }
    ],
  },
  {
    version: "v2.16.0",
    date: "March 15, 2026",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Completely rewrite the program structure to closer align with a standard Python project layout",
            children: [
              {
                html: "<b>IMPORTANT</b>: All non-Docker users need to update their launch command to start TCM. See <a href=\"https://titlecardmaker.com/#updating\" target=\"_blank\" rel=\"noopener noreferrer\">the docs</a> for details."
              },
              {
                html: "Move the <b>app</b> folder into <b>backend</b>, remove the <b>modules</b> folder"
              },
              {
                html: "Move the <b>app/templates</b> folder into <b>frontend</b>"
              },
              {
                html: "Move the <b>cypress</b> testing directory into <b>tests/cypress</b>"
              },
              {
                html: "Rewrite all application logging (see below)"
              },
              {
                html: "Change all API routes to be versioned and include <b>/v2/</b>"
              },
              {
                html: "Move all card type assets to <b>backend/assets/...</b> - if you have developed a custom card type file these references will need to be updated (I have already updated all those which were submitted to the Card Type repository)"
              }
            ]
          },
          {
            html: "Completely overhaul the Scheduler to use <b>huey</b> instead of <b>apscheduler</b>",
            children: [
              {
                html: "<b>apscheduler</b> was prone to \"breaking\" by locking a Task's next execution in the past, and did not have nice-to-have features like thread locking, state persistence, etc."
              },
              {
                html: "The Scheduler will now run in a separate thread from the main TCM server"
              },
              {
                html: "No longer allow scheduling Task frequencies with basic intervals (i.e. <b>5 hours</b>) in basic mode; instead all scheduling must be done with crontab strings"
              }
            ]
          },
          {
            html: "Various improvements to the Add Series page",
            children: [
              {
                html: "Improve page layout with more consistent styling and positioning of various buttons"
              },
              {
                html: "Add help messages to each section to guide new users"
              },
              {
                html: "Redesign the Blueprint HTML elements to use popups instead of unexplained buttons",
                children: [
                  {
                    image: "https://github.com/user-attachments/assets/a16d7165-bf47-4ab5-ba10-a517e9e6d796",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Various improvements to the home page filters",
            children: [
              {
                html: "Preserve the currently applied filter between reloads"
              },
              {
                html: "Add the ability to stop applying all filters on the home page"
              },
              {
                html: "Add the ability to delete a single filter condition from the home page"
              },
              {
                html: "Add length filter conditions - i.e. <b>has more items than</b>, and <b>has less items than</b> for filtering by list length and <b>text is longer than</b> and <b>text is shorter than</b> for filtering by string length"
              }
            ]
          },
          {
            html: "Create new <i>Dictionary</i> card type",
            children: [
              {
                html: "All documentation is available <a href=\"https://titlecardmaker.com/card_types/dictionary/\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>",
                children: [
                  {
                    image: "https://titlecardmaker.com/card_types/assets/dictionary.webp",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Create new <i>Anime Fade</i> card type - this was requested by user drewstopherlee",
            children: [
              {
                html: "All documentation is available <a href=\"https://titlecardmaker.com/card_types/anime_fade/\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>",
                children: [
                  {
                    image: "https://titlecardmaker.com/card_types/assets/anime_fade.webp",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Improve the Graphs page",
            children: [
              {
                html: "Add an improved filter options section"
              },
              {
                html: "Label each graph",
                children: [
                  {
                    image: "https://github.com/user-attachments/assets/31222926-a167-4c9c-a034-5c60a7208954",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Various improvements to the Recent page",
            children: [
              {
                html: "Add buttons to quickly display Cards created in the last 6 hours, 24 hours, or 7 days"
              },
              {
                html: "Now display recently added Series, in addition to recently created Title Cards"
              }
            ]
          },
          {
            html: "Change the default card type to <i>Tinted Frame</i> - this is (seemingly) the most popular card design. This change only affects new TCM users, and does not change the default card type of existing users"
          },
          {
            html: "No longer \"pickle\" global settings - these are now stored as plain JSON at <b>config/settings.json</b>"
          },
          {
            html: "Add the ability to selectively re/load Cards for entire <i>seasons</i>, as opposed to individual Episodes or the entire show"
          },
          {
            html: "Display the temporary credentials within the UI when first enabling authentication"
          },
          {
            html: "Add some commonly useful system actions to the home page - these currently are starting Card creation, Card loading, and importing Kometa YAML"
          },
          {
            html: "Display unloaded Cards on the frontend on the Missing page"
          },
          {
            html: "Significantly improve the performance of the SQL query when displaying Series with the associated Episode/Loaded counts - this should be an approximate 100x performance increase"
          },
          {
            html: "Completely remove all v1/YAML-related code",
            children: [
              {
                html: "This removes all backwards compatibility with those running v1 on the v2 repository"
              },
              {
                html: "This was done in order to significantly simplify the codebase"
              }
            ]
          },
          {
            html: "Rewrite all environment variables used to significantly change the behavior of TCM - see <a href=\"TODO\" target=\"_blank\" rel=\"noopener noreferrer\">docs</a> for more details"
          },
          {
            html: "Update the Font and Template Card previews to select a specific Episode to preview, so Series and Episode level customizations can be viewed concurrently"
          },
          {
            html: "Update the Font missing character analysis to utilize ImageMagick to actually check for empty or missing character bitmaps, rather than looking at the character definition table (as some Fonts would \"define\" a blank character which would not be reported missing)"
          },
          {
            html: "Completely rewrite application logging",
            children: [
              {
                html: "Log to an SQL database, not JSONL files - this will significantly improve performance when querying logs"
              },
              {
                html: "Remove hard-coded contextualized logger arguments in all functions, rather attach log objects directly to the process using the builtin <b>contextvars</b> package - this effectively adds auto contextualization across the entire application"
              },
              {
                html: "Display a 'pretty' log message table for STDOUT logs"
              },
              {
                html: "Add the ability to prune (delete) logs from the frontend to aid in sending large log databases via Discord or GitHub"
              }
            ]
          },
          {
            html: "Do not immediately delete un-Synched Series (when enabled on the Settings page) until <i>10 days</i> (this can be changed via an environment variable) of being gone. This is enabled to prevent database \"blips\" from Sonarr/Plex/etc. from resulting in TCM completely deleting a large number of Series"
          },
          {
            html: "Add a \"thank you\" banner to the page header to show thanks to all the wonderful supports of this project"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Allow selecting the <b>does not equal</b> filter condition on the home page"
          },
          {
            html: "Handle Title Cards without an assigned Series or Episode on the Recently Added page"
          },
          {
            html: "Fix season poster loading For Emby - was incorrectly loading Season 0 into 1, 1 into 2, etc, if there was no Specials season"
          },
          {
            html: "Fix editing the currently assigned Templates for a given Sync via the API - was incorrectly resetting the Template ID assignments with each edit"
          },
          {
            html: "Properly display the Image Source Priority setting in the correct ID order, not ascending - i.e. <b>2,1,3</b> was displaying as <b>1,2,3</b>"
          },
          {
            html: "Properly delete existing Episodes from season 0 when these are disabled for a given Series <i>but</i> still present in the assigned Episode Data Source"
          },
          {
            html: "Reduce false positive Series and Episode matches by modifying the match algorithm to require one of:",
            children: [
              {
                html: "Any <i>two</i> database ID matches"
              },
              {
                html: "An exact name and year match"
              },
              {
                html: "Any single database ID match <i>and</i> either an exact name or year match"
              }
            ]
          },
          {
            html: "Fix uploading per-season backdrop assets via the UI"
          },
          {
            html: "Prevent significant page flashes from white to black when swapping pages in the UI"
          },
          {
            html: "Pin documentation build workflow Python version to 3.13.7 (3.14 is not supported by Pillow)"
          },
          {
            html: "Handle exceptions due to bad image downloads for posters/logos when adding a Series"
          },
          {
            html: "Completely rewrite the Emby, Jellyfin, and Sonarr API interface classes to work on validated Pydantic models to improve reliability"
          },
          {
            html: "Fix required root folder Sync filters for syncing from Sonarr"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Allow searching for Blueprints by Series name on the Series page Blueprints tab, then importing a matching Blueprint into the current Series"
          },
          {
            html: "Use Python 3.13 in the Docker container instead of 3.11 - I recommend non-Docker users update to 3.13 as well"
          },
          {
            html: "Add keyboard navigation to the Episode Data table on the Series page - use tab, shift+tab, up arrow, and down arrow to navigate between columns/rows of the table"
          },
          {
            html: "Store the uploaded file as the Source Image (in addition to the card file) when uploading cards as \"textless\""
          },
          {
            html: "Allow directly adding a library to a Series when added via the add-Series Sonarr webhook by including the <b>connection_id</b> query parameter to the Webhook URL"
          },
          {
            html: "Display a page loader on the Recently Created page while Cards are being queried"
          },
          {
            html: "Use improved Episode data endpoints on the Series page to improve performance especially when using simplified data tables"
          },
          {
            html: "Use reduced data queries on the Missing Cards page to improve performance"
          },
          {
            html: "No longer allow sorting <i>just</i> the currently visible page of Series on the home page"
          },
          {
            html: "Print ImageMagick command history when booting and determining command prefix"
          },
          {
            html: "Log remote file download failures"
          },
          {
            html: "Upgrade <b>pydantic</b> dependency to v2"
          },
          {
            html: "Rewrite command line scripts to work with <b>click</b>, rather than builtin <b>argparse</b>"
          },
          {
            html: "Improve the performance on the Fonts page for very large setups by only initializing the Font accordions for elements as they are expanded"
          },
          {
            html: "Log bad format strings as DEBUG messages, not ERROR"
          },
          {
            html: "Modify the Add Series and Settings pages to provide visual feedback if no Connections have been defined yet"
          },
          {
            html: "Store how long each Task takes in the database"
          },
          {
            html: "Remove the Import page from the front end"
          },
          {
            html: "Display a message when there are no recently made Title Cards on the Recent page"
          },
          {
            html: "Improve the navigation layout on the Changelog page"
          },
          {
            html: "Add the ability to delete a Series' logo on the front end"
          },
          {
            html: "Improve the layout of the Sync page by displaying some details in an expandable details section for each Sync"
          },
          {
            html: "Query card type data from the appropriate develop-specific branch when TCM is on the develop branch; this will enable future flexibility for modifying Card Types on the fly without affecting stable users"
          },
          {
            html: "Change the default log level to TRACE when first loading the logs page"
          },
          {
            html: "Change the available page size options on the logs page"
          },
          {
            html: "Display Connection validation errors in the form when bad parameters are submitted"
          },
          {
            html: "Change the toolbar theme/logs/help button sizes"
          },
          {
            html: "Completely rewrite the TVDb interface to work with validated data models and significantly improve reliability and uncaught exceptions due to bad data"
          },
          {
            html: "Delete a Series' card directory (if empty) when deleting a Series"
          },
          {
            html: "Add the ability to download a zip of a Series' Title Cards directly from the frontend"
          },
          {
            html: "Add new format string functions and variables",
            children: [
              {
                html: "<b>to_lowercase(...)</b> as an alternate to <b>str.lower()</b>"
              },
              {
                html: "<b>to_uppercase(...)</b> as an alternate to <b>str.upper()</b>"
              },
              {
                html: "<b>{</b> and <b>}</b> as <b>OPEN_BRACKET</b> and <b>CLOSE_BRACKET</b>"
              },
              {
                html: "Blank text (<b>{\"\"}</b>) as <b>BLANK</b>"
              },
              {
                html: "Add a new optional <b>timezone</b> argument to the <b>format_date</b> function"
              }
            ]
          },
          {
            html: "Improve the extra accordions on the Series page by only displaying the card types which are currently \"active\" (i.e. selected by any Series/Template/etc.)"
          },
          {
            html: "Use an improved formatting (using <b>rich</b>) to log ImageMagick command histories"
          },
          {
            html: "Improve the error messages displayed for invalid extras when using custom validator logic"
          },
          {
            html: "Improve the logging when launching the program with a bad encryption key"
          },
          {
            html: "Stop using animated save/submit buttons"
          },
          {
            html: "Add a \"helper\" for available card type details to the Series and Template pages"
          },
          {
            html: "Keep the last-used MediUX import settings between reloads (stored in the browser)"
          },
          {
            html: "Add a button to delete a Template condition - the previous method was to just leave this blank"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Do not remove the missing Card table headers when populating the missing Cards table"
          },
          {
            html: "Do not stop all Card imports if an OS error occurs for any single file"
          },
          {
            html: "Handle YAML imports without backdrop/poster URLs"
          },
          {
            html: "Properly remove deleted Series from the page when bulk-deleting Series on the home page"
          },
          {
            html: "Do not reject matching library path names for Sonarr Connections if they are for the same library"
          },
          {
            html: "Improve handling of TVDb API errors when querying Episode data (usually caused by bad TVDb IDs)"
          },
          {
            html: "Do not query all \"duplicate\" interfaces for database IDs - just query the first Sonarr, TMDb, and TVDb interface"
          },
          {
            html: "Display missing Title Cards in improved order - these were being returned by the SQL default order (Episode ID) - now these are sorted by Series, then index"
          },
          {
            html: "Improve the <b>start.sh</b> script handling of being launched as a non-root user"
          },
          {
            html: "Handle empty string URLs when uploading Source Images via the frontend"
          },
          {
            html: "Properly reset the Episode Data table pagination when all Episodes are deleted on the frontend"
          },
          {
            html: "Properly query Series-related log messages using the <b>|</b> separator"
          },
          {
            html: "Pin Python version between 3.12 and 3.13 as 3.14 has not been supported by a few dependent packages"
          },
          {
            html: "Do not require a TMDb connection to browse Source Images on the frontend"
          },
          {
            html: "Do not throw errors when visiting the Add Series page with no defined Connections"
          },
          {
            html: "Fix downloading Source Images from Emby or Jellyfin via the UI"
          },
          {
            html: "Handle MediUX error strings in image downloading"
          },
          {
            html: "Allow resetting non-list fields to their default value when editing Syncs on the frontend"
          },
          {
            html: "Do not raise an error for disabled/bad library Connections when downloading a Series poster or logo"
          },
          {
            html: "Add some logic to prevent adding Series which already exist in the database (should prevent some duplication when incorrectly running multiple Syncs at once)"
          },
          {
            html: "Prevent displaying \"stale\" extra info when editing an Episode's extras by navigating back-and-forth between modals"
          },
          {
            html: "Change the MediUX download timeout to 15 seconds"
          },
          {
            html: "Allow deleting a Font's character replacement by clearing the input string box"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "All Card Types",
            children: [
              {
                html: "Add a pre-card creation \"hook\" (like React) so custom card types may implement <b>enrich_card_data()</b> as a static method to add arbitrary dynamic extras to a Card"
              },
              {
                html: "This is currently used in the Dictionary card to automatically pull in an Episode's overview"
              }
            ]
          },
          {
            html: "Create new <i>Anime Fade<i>and</i>Dictionary</i> card types"
          },
          {
            html: "Cascade",
            children: [
              {
                html: "Properly handle characters which need escaping (<b>\"</b>, <b>\\</b>, etc.) in the alternate text"
              }
            ]
          },
          {
            html: "Divider",
            children: [
              {
                html: "Rename the Title Text Position extra to Title Text Side to improve clarity"
              },
              {
                html: "Add new Divider Width extra"
              },
              {
                html: "Improve divider height calculation algorithm to be more accurate for multi-line text"
              }
            ]
          },
          {
            html: "Formula 1",
            children: [
              {
                html: "Change the default frame year to 2026"
              }
            ]
          },
          {
            html: "Inset",
            children: [
              {
                html: "Improve the positioning of inset text - this <i>was</i> being positioned using the \"old\" annotation text measurement method, but now uses the explicit image size measurement algorithm to exactly center the text"
              }
            ]
          },
          {
            html: "Landscape",
            children: [
              {
                html: "Add blur box, rounding radius, and box blur extras"
              },
              {
                html: "Use improved text measurement algorithm to improve dynamic padding when using non-default Fonts"
              }
            ]
          },
          {
            html: "Poster",
            children: [
              {
                html: "Add \"Episode Text Font Size\" extra"
              }
            ]
          },
          {
            html: "Roman Numeral",
            children: [
              {
                html: "Add season text size extra"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Prefer <b>{font_file}</b> in the Episode Text Font File extra instead of <b>{title_font}</b> - the \"old\" <b>{title_font}</b> is still supported for backwards compatibility, but will log a message"
              }
            ]
          },
          {
            html: "Remote Card Type Changes",
            children: [
              {
                html: "Create a helper <b>RemoteDirectory</b> class for easily referencing a directory on the Card Type repository and using it for multiple files"
              },
              {
                html: "Move the Card Type repository to the TitleCardMaker organization - the new repository is <a href=\"https://github.com/TitleCardMaker/CardTypes\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
              },
              {
                html: "Rewrite how all custom card types need to define their default card settings, see the documentation for details"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Document all remaining card types"
          },
          {
            html: "Adjust recommended Sync source from Sonarr to your primary media server - this is because many users incorrectly set up the library setting for Sonarr, which can lead to confusion"
          },
          {
            html: "Document the recently added Logo-related extras for the Anime card type"
          },
          {
            html: "Add step to install Python to the Getting Started docs"
          },
          {
            html: "Correct webhook docs for Sonarr integration to reference the \"On File Import\" section"
          },
          {
            html: "Finish documenting the Series page"
          },
          {
            html: "Document all available environment variables"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Modify the add-Series webhook (<b>/api/webhooks/sonarr/series/add</b> or <b>/api/v2/webhooks/sonarr/series/add</b>) to take the <b>connection_id</b> URL query parameter"
          },
          {
            html: "Remove deprecated <b>GET</b> <b>/api/cards/missing</b> - use the <b>GET</b> <b>/api/v2/missing/cards</b> endpoint instead",
            children: [
              {
                html: "This endpoint now returns the revised <b>ReducedEpisodeData</b> schema (for faster loads)"
              }
            ]
          },
          {
            html: "Remove deprecated <b>GET</b> <b>/api/settings/backups</b> - use the <b>GET</b> <b>/api/v2/backups/all</b> endpoint instead"
          },
          {
            html: "Remove deprecated <b>PUT</b> <b>/api/cards/series/{series_id}/load/library</b> endpoint"
          },
          {
            html: "Create new API endpoints to get a Series' Episode data",
            children: [
              {
                html: "Deprecate the <b>GET</b> <b>/api/episodes/series/{series_id}</b> endpoint"
              },
              {
                html: "Create <b>GET</b> <b>/api/v2/episodes/series/{series_id}/extended</b> to get \"extended\" Episode data which has all fields of all Episodes"
              },
              {
                html: "Create <b>GET</b> <b>/api/v2/episodes/series/{series_id}/simplified</b> to get simplified data"
              },
              {
                html: "Remove <b>cards</b> attribute from Episode return schema"
              }
            ]
          },
          {
            html: "Add <b>sort_name</b> to the Font and Template availability API endpoints"
          },
          {
            html: "Standardize various Font and Template API endpoints",
            children: [
              {
                html: "<b>POST</b> <b>/api/fonts/new</b> is now <b>POST</b> <b>/api/v2/fonts/font/new</b>"
              },
              {
                html: "<b>PUT</b> <b>/api/fonts/{font_id}/file</b> is now <b>PUT</b> <b>/api/v2/fonts/font/{font_id}/file</b>"
              },
              {
                html: "<b>DELETE</b> <b>/api/fonts/{font_id}/file</b> is now <b>DELETE</b> <b>/api/v2/fonts/font/{font_id}/file</b>"
              },
              {
                html: "<b>PATCH</b> <b>/api/fonts/{font_id}</b> is now <b>PATCH</b> <b>/api/v2/fonts/font/{font_id}</b>"
              },
              {
                html: "<b>GET</b> <b>/api/fonts/{font_id}</b> is now <b>GET</b> <b>/api/v2/fonts/font/{font_id}</b>"
              },
              {
                html: "<b>GET</b> <b>/api/fonts/{font_id}/analysis</b> is now <b>GET</b> <b>/api/v2/fonts/font/{font_id}/analysis</b>"
              },
              {
                html: "Similar endpoint revisions have been made to the Templates router"
              }
            ]
          },
          {
            html: "Revise the Series/Episode schemas to combine the <b>extras</b> and <b>season_titles</b> fields, rather than have separate fields which are processed into one"
          },
          {
            html: "Do not paginate the get all Templates API endpoint"
          },
          {
            html: "Update the <b>GET</b> <b>/api/statistics/snapshots</b> endpoint",
            children: [
              {
                html: "New endpoint is <b>GET</b> <b>/api/v2/statistics/snapshots</b>"
              },
              {
                html: "Remove the <b>previous_days</b> and <b>previous_hours</b> query parameters"
              },
              {
                html: "Add new <b>start</b> and <b>end</b> query parameters"
              }
            ]
          },
          {
            html: "Create new <b>GET</b> <b>/api/v2/logs/database-zip</b> endpoint to get a zip of the log database"
          },
          {
            html: "Rename <b>/schedule/</b> router to <b>/scheduler/</b> - this affects all endpoints"
          },
          {
            html: "Create new <b>GET</b> <b>/api/v2/missing/cards-without-loaded</b> endpoint to get all Cards which do not have an associated Loaded asset"
          },
          {
            html: "Excluded \"blacklisted\" Blueprints from the Blueprint query by info API endpoint"
          },
          {
            html: "Add <b>order_by</b> query parameter to the <b>GET</b> <b>/api/v2/blueprints/query/series</b> endpoint to order by the creation date or Series name"
          },
          {
            html: "Create new <b>GET</b> <b>/api/v2/series/recent</b> API endpoint to get all the Series added after a given datetime"
          },
          {
            html: "Properly raise an 404 error when querying by a Title Card ID which does not exist"
          },
          {
            html: "Properly implement the pipe (<b>|</b>) separator when querying for logs which contain a specific substring"
          },
          {
            html: "Create new <b>POST</b> <b>/api/v2/import/mediux</b> endpoint to import arbitrary Kometa/MediUX YAML via the builtin TVDB ID"
          },
          {
            html: "Create new <b>DELETE</b> <b>/api/v2/logs/prune</b> endpoint to prune old log messages from the database to reduce the log database size - this is also done within a scheduled Task"
          },
          {
            html: "Remove all v1/YAML-import related API endpoints"
          },
          {
            html: "Create new <b>POST</b> <b>/api/v2/cards/preview/episode/{episode_id}</b> and <b>/api/v2/cards/preview/episode/{episode_id}/template/{template_id}</b> endpoints to get a Card preview for the changes to a specific Episode <i>or_ Template - the old <b>/api/cards/preview</b> endpoint has been __removed_</i> (not deprecated)"
          }
        ]
      },
      {
        title: "Testing Changes",
        items: [
          {
            html: "Create spoofed Interface returns for use in frontend tests - these are dynamically injected into the Interface classes when test mode is enabled"
          },
          {
            html: "Rewrite scheduler tests to work with the new crontab style of scheduling Tasks"
          },
          {
            html: "Remove navigation tests related to the Import page"
          },
          {
            html: "Write tests for the Connections, Settings, Sync, Add Series / Blueprint, and Font pages"
          },
          {
            html: "Change the default dimensions of the testing viewport to 1920x1080"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.15.0",
    date: "April 27, 2025",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add native support to extract colors from an image and use it in Format Strings and colors",
            children: [
              {
                html: "<b>get_image_color</b> can be used in any extras which support Format Strings - like so: <b>{get_image_color(logo_file, fallback='white')}</b> would get the first (primary) color of the logo file - and if one cannot be determined (or is too white/black) then white is used instead"
              },
              {
                html: "This is documented <a href=\"https://titlecardmaker.com/user_guide/variables/#parse-image-color\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
              }
            ]
          },
          {
            html: "Add a quick-toggle button to the Series page to swap between advanced and basic mode for the Episode data tables"
          },
          {
            html: "Improve watched status and style-toggles in Card creation",
            children: [
              {
                html: "Properly assign a card's style if the watched status is indeterminate"
              },
              {
                html: "Properly use style-specific Source Images if the watched status is indeterminate"
              }
            ]
          },
          {
            html: "Add the ability to mass-remove libraries from all Series",
            children: [
              {
                html: "This can be done to automatically remove all \"unlinked\" libraries (typically as a result of typing a bad library name in a Sonarr Sync), or to remove all assignments of a valid library"
              }
            ]
          },
          {
            html: "Create a new \"Recently Added\" page which displays all recently created Title Cards",
            children: [
              {
                html: "Accessed at <b>/recent</b>, or via the sidebar"
              },
              {
                html: "Requires SQL schema <b>e290ff7005ff</b> to add creation timestamp columns to various tables"
              },
              {
                html: "Existing objects will be populated with \"fake\" (but sequential) creation timestamps - but objects added/created after this change will be accurate",
                children: [
                  {
                    image: "https://titlecardmaker.com/user_guide/assets/recent-dark.webp#only-dark",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Allow <b>all</b> card settings to be specified as Format Strings",
            children: [
              {
                html: "This means any setting (including extras) can use the dynamic/conditional logic and variables available to explicit format strings like the episode text format, filename format, etc."
              },
              {
                html: "For example, rather than creating a custom Template with conditions to change the font color based on a season, this can be done by setting the Font Color setting to (for example) <b>{\"red\" if season_number == 0 else \"blue\"}</b>"
              }
            ]
          },
          {
            html: "Add button to query/display all \"missing\" Series in a given Connection not added to TCM - this is currently untested for Emby or Jellyfin"
          },
          {
            html: "Allow a Series to be completely disabled",
            children: [
              {
                html: "A Series can now have a \"Status\" of Monitored, Unmonitored, or Disabled"
              },
              {
                html: "Unmonitored Series will not add new content (Source Images, translations, etc.) but still maintain up-to-date Cards; Disabled Series will be completely ignored during all scheduled Tasks (Card creation, poster downloads, etc.)"
              },
              {
                html: "Requires SQL schema <b>f4afea8860cf</b> to migrate <b>Series.monitored</b> to <b>Series.status</b>"
              },
              {
                html: "Existing Series filters on the home page which refer to the <b>Monitored Status</b> field will be removed and should be replaced with a variation of the <b>Series Status</b> filter"
              },
              {
                html: "Toggling a Series' status works generally the same, but now cycles through Monitored -> Unmonitored -> Disabled -> (loop)"
              },
              {
                html: "Disabling any Series which you do not plan to adjust or add content to <i>at all</i> can significantly speed up TCM"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix the alternate gradient overlay in the Olivier card"
          },
          {
            html: "Handle null episode titles from TVDb"
          },
          {
            html: "Manually editing Episode translations within the UI no longer deletes the translation completely"
          },
          {
            html: "Fix a mismatch of Episodes with the same index and airdate from different Series causing the Plex webhook to incorrectly fail"
          },
          {
            html: "Require Source Images in the Textless card - this should fix the setup in which users are using the Textless card <i>by default</i> - e.g. only applying un/watched styles"
          },
          {
            html: "Correctly utilize the local <b>TZ</b> timezone when storing Task start/end times"
          },
          {
            html: "Add rudimentary library path validation when editing Sonarr connections - TCM will now check if one library path contains another, e.g. <b>/path/1</b> and <b>/path/12</b>"
          },
          {
            html: "Reset Series selection on the home page when performing batch status changes"
          },
          {
            html: "Add pagination to the Missing Cards page/table"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add ability to re-download a Series' poster via the UI"
          },
          {
            html: "Significantly improve the Episode match algorithm to require at least 2 exact database ID matches, or an index match and either a title, single database ID, or airdate match"
          },
          {
            html: "Relocate the log context ID field on the logs tab of the Series page"
          },
          {
            html: "Trace log bad image content when downloading images"
          },
          {
            html: "Allow adding <b>!</b> to a context ID filter string to remove all non-contextual log messages when filtering logs"
          },
          {
            html: "Contextually blur unrelated log messages when hovering over a context ID on the logs tab of the Series page"
          },
          {
            html: "Display the relevant database IDs for Series displayed on the Add Series page"
          },
          {
            html: "Use improved (faster) slicing when querying Snapshots - no longer query all results and then slice the list in Python; instead use a SQL subquery to slice directly"
          },
          {
            html: "Change the \"Remove Counts\" button text to \"Hide Counts\""
          },
          {
            html: "Add loading indicator when querying logs on the Logs page"
          },
          {
            html: "Display an info message to indicate there are no internal server logs"
          },
          {
            html: "Begin tracking how long scheduled Tasks take",
            children: [
              {
                html: "This requires SQL schema <b>753b403e12d2</b> to create the <b>task_durations</b> table"
              },
              {
                html: "These can now be displayed on the Graphs page",
                children: [
                  {
                    image: "https://github.com/user-attachments/assets/a5591c3e-4b81-4d35-92e9-daa285d3e07a",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Display an error within the UI if a manual Card loading fails"
          },
          {
            html: "Add daily vertical axis lines on the Graphs page (to delineate days)"
          },
          {
            html: "Add button to the Source Image popup to quickly set an Episode's card type to Textless"
          },
          {
            html: "Display loading icons on the home page when performing actions on a Series"
          },
          {
            html: "Add new \"has no Episodes\" Series filter condition"
          },
          {
            html: "v1 Update the \"Created by TitleCardMaker\" image used in summary image creation"
          },
          {
            html: "v1 Add a mini maker command for batch show summary creation"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Properly assign unwatched flag when new Episodes are added via Sonarr webhook"
          },
          {
            html: "Remove the scroll overflow for posters on the Add Series page"
          },
          {
            html: "Improve the Series sort name logic to account for non-alphanumeric characters (including Unicode and &)"
          },
          {
            html: "Force expire the request cache when manually refreshing remote card type data"
          },
          {
            html: "Log server start time in localized timezone"
          },
          {
            html: "Improve handling of \"bad\" IMDb ID's not formatted as <b>tt____</b> in the database source"
          },
          {
            html: "Properly delete Card records from the database when removing Episodes which are no longer in the Episode Data Source"
          },
          {
            html: "v1 Fix manual summary image creation with the mini maker"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Allow positioning a logo on the Anime card type; adding the logo position and size extras"
              }
            ]
          },
          {
            html: "Cutout",
            children: [
              {
                html: "Add title horizontal shift extra"
              }
            ]
          },
          {
            html: "Fade",
            children: [
              {
                html: "Add logo size extra"
              }
            ]
          },
          {
            html: "Landscape",
            children: [
              {
                html: "Correctly utilize custom darken and shadow colors (were being ignored)"
              }
            ]
          },
          {
            html: "Logo",
            children: [
              {
                html: "Add new logo horizontal shift extra"
              }
            ]
          },
          {
            html: "Skeleton Crew",
            children: [
              {
                html: "Fix text sizing on some versions of ImageMagick"
              }
            ]
          },
          {
            html: "Tinted Glass",
            children: [
              {
                html: "Fix right-positioned episode text"
              },
              {
                html: "Limit glass adjustments between -300 and 300 pixels on any face"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Added documentation on Jellyfin Webhook integration"
          },
          {
            html: "Document mass library deletion interactions"
          },
          {
            html: "Correct documentation on how to disable season subfolders"
          },
          {
            html: "Update <a href=\"https://titlecardmaker.com/user_guide/variables/\" target=\"_blank\" rel=\"noopener noreferrer\">Variables</a> docs to reflect the ability to use variables/format strings in any card setting"
          },
          {
            html: "Add documentation on the <b>backdrop_file</b>, <b>logo_file</b>, and <b>poster_file</b> file variables"
          },
          {
            html: "Document new <b>get_image_color()</b> function"
          },
          {
            html: "Create new page on the <a href=\"https://titlecardmaker.com/user_guide/recent/\" target=\"_blank\" rel=\"noopener noreferrer\">Recently Added</a> page"
          },
          {
            html: "Create new page on the <a href=\"https://titlecardmaker.com/user_guide/missing/\" target=\"_blank\" rel=\"noopener noreferrer\">Missing Summary</a> page"
          },
          {
            html: "Document use of the <b>!</b> in log context ID filters"
          },
          {
            html: "Create pages on various card types:",
            children: [
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/marvel/\" target=\"_blank\" rel=\"noopener noreferrer\">Marvel</a>"
              },
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/cutout/\" target=\"_blank\" rel=\"noopener noreferrer\">Cutout</a>"
              },
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/tinted_glass/\" target=\"_blank\" rel=\"noopener noreferrer\">Tinted Glass</a>"
              }
            ]
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Create API endpoint to delete library references from all Series",
            children: [
              {
                html: "<b>DELETE</b> <b>/api/connections/{id}/libraries</b> can accept either an <b>unlinked</b> boolean query to delete all unlinked libraries (e.g. those not present in the current library list), or a <b>library_name</b> string query to delete all references to a specific library"
              }
            ]
          },
          {
            html: "Create <b>GET</b> <b>/api/cards/recent</b> API endpoint to get all Title Cards which were created after a specified date/time"
          },
          {
            html: "Create <b>DELETE</b> <b>/api/series/series/{series_id}/poster</b> endpoint to delete a Series poster"
          },
          {
            html: "Raise <b>400</b> exceptions if card loading fails in various Card loading endpoints"
          },
          {
            html: "Create <b>GET</b> <b>/api/statistics/task-durations</b> endpoint to query task run durations"
          },
          {
            html: "Create <b>GET</b> <b>/api/missing/series</b> to get all Series in a given Connection which are <i>not</i> added to TCM"
          },
          {
            html: "API changes to reflect new Series <b>status</b> field",
            children: [
              {
                html: "All <b>Series</b>-related models no longer return the <b>monitored</b> boolean field, now returning the <b>status</b> string"
              },
              {
                html: "Deprecate <b>PUT</b> <b>/api/series/batch/monitor</b> and <b>/api/series/batch/unmonitor</b> endpoints"
              },
              {
                html: "Create new <b>PATCH</b> <b>/api/series/batch/status/{status}</b> endpoint"
              },
              {
                html: "Change behavior of <b>PUT</b> <b>/api/series/{series_id}/toggle-monitor</b> endpoint to now cycle through statuses"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.14.1",
    date: "January 27, 2025",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Create new Cascade card type - this card can also have Kanji added to it"
          },
          {
            html: "Add new Skeleton Crew card type (created by Supremicus)",
            children: [
              {
                image: "https://titlecardmaker.com/card_types/assets/skeleton_crew.webp",
                width: "50%"
              }
            ]
          },
          {
            html: "Improve Plex API call performance",
            children: [
              {
                html: "Include Episode GUIDs in the initial API call to Plex to improve Episode match timings (and reduce the need for an API call for each GUID comparison)"
              },
              {
                html: "Fast-exit when matching Episodes for Card loads; this means loading subsets of Title Cards should be much faster"
              }
            ]
          },
          {
            html: "Add functionality to upload multiple (generic) Source Images directly to a Series source directory"
          },
          {
            html: "Begin implementation of mask image editing and creation as part of TCM"
          },
          {
            html: "Significantly improve the speed of Series searching"
          },
          {
            html: "Update Episode airdate when refreshing Episode data"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Properly display very long exception log messages on the log page"
          },
          {
            html: "Do not reinitialize the HTML <b>template</b> elements when creating a new Template"
          },
          {
            html: "Properly display sequential non-alphabetical Templates in dropdowns on the Series page"
          },
          {
            html: "Fix adding the global card type to Blueprint exports only if one is not defined an an associated Template"
          },
          {
            html: "No longer allow selecting Sonarr Connections in Series Image Source Priority dropdowns"
          },
          {
            html: "Fix changing the Font title case setting on the Series page"
          },
          {
            html: "Implement the <b>Has Missing Title Cards is false</b> Series filter condition (was no-op)"
          },
          {
            html: "Improve Episode database ID match logic for Plex - require at least one <i>net</i> positive ID match, this means that Episodes which have just one matching ID, but other mismatching ID's (e.g. matching IMDb, not matching TMDb and TVDb IDs) do not falsely flag"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add Download buttons to Source Images on the Series page"
          },
          {
            html: "Add new variables for format strings in Card creation:",
            children: [
              {
                html: "<b>number_of_seasons</b> which is the number of unique seasons a Series has"
              },
              {
                html: "Python's builtin <b>len()</b> and <b>locals()</b> functions"
              },
              {
                html: "Change <b>airdate</b> and <b>absolute_number</b> to always be present even if undefined; if no set airdate or no defined absolute number then these default to <b>None</b>"
              }
            ]
          },
          {
            html: "Log unmatched Episodes when loading Cards into Plex"
          },
          {
            html: "Improve font replacement query logic for globally assigned Fonts (by querying all titles for characters to replace)"
          },
          {
            html: "Reword some Task descriptions on the Scheduler page to improve clarity"
          },
          {
            html: "Log when refreshing Episode data during the Plex webhook"
          },
          {
            html: "Sleep for 5 seconds before refreshing Episode data for missing Episodes in Plex webhooks"
          },
          {
            html: "Change the default interval of the card data refresh task to 3 days (from 1)"
          },
          {
            html: "Revise parts of the Graphs page",
            children: [
              {
                html: "Remove the data point styling"
              },
              {
                html: "Change the graph styling to stepwise (instead of interpolation)"
              },
              {
                html: "Adjust the fill styling"
              }
            ]
          },
          {
            html: "Improve the error messages for creating previews using uninitialized remote card types"
          },
          {
            html: "Allow specification of the <b>TCM_CARD_TYPE_URL</b> environment variable to override the root URL of remote card types - this is designed to make it easier to test remote card types while they are developed."
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Improve handling of bad / invalid TVDb IDs when querying for Episode or Source Image data from TVDb"
          },
          {
            html: "Handle more types of bad TMDb ID's from Emby"
          },
          {
            html: "Improve handling of TMDb 404 errors in Source Image queries"
          },
          {
            html: "Properly enable editable reference fields for existing filters on the home page"
          },
          {
            html: "Fix Template <b>is not null</b> filter condition assignment from the UI"
          },
          {
            html: "Properly assign a Series' TVDb ID (instead of TMDb ID) when searching for Series via TVDb"
          },
          {
            html: "Improve handling of null episode data when querying TVDb"
          },
          {
            html: "Avoid FE cache collisions for Cards whose size does not change, but is remade"
          },
          {
            html: "v1 Fix SVG to PNG logo conversion"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "All types",
            children: [
              {
                html: "Create an improved (and very accurate) <b>ImageMagick.get_text_label_dimensions</b> method to get the exact dimensions of some <b>label:</b> generated ImageMagick text while accounting for exact dimensions not FontTools reported metrics"
              },
              {
                html: "Rename the <b>BaseCardType.SEASON_TEXT_FORMATTER</b> class method to <b>season_text_formatter</b> (functional spec remains unchanged)"
              },
              {
                html: "Change the <b>BaseCardType.resolve_format_strings</b> method two accept a single dictionary (<b>data: dict</b>) rather than unpacked keyword arguments (<b>**data</b>)"
              },
              {
                html: "Move all card type validator models into their respective card Python files, rather than <b>app.schemas.card_type</b>"
              }
            ]
          },
          {
            html: "Calligraphy",
            children: [
              {
                html: "Fix episode text hiding"
              }
            ]
          },
          {
            html: "Comic Book",
            children: [
              {
                html: "Fix the episode text box fill color extra (was incorrectly using the title text box fill color)"
              }
            ]
          },
          {
            html: "Fade",
            children: [
              {
                html: "Add episode text font size extra"
              }
            ]
          },
          {
            html: "Formula 1",
            children: [
              {
                html: "Fix the country flag determination logic"
              }
            ]
          },
          {
            html: "Music",
            children: [
              {
                html: "Handle Percentage format strings which resolve to <b>random</b>"
              }
            ]
          },
          {
            html: "Olivier",
            children: [
              {
                html: "Add new gradient type extra"
              }
            ]
          },
          {
            html: "Score",
            children: [
              {
                html: "Fix the default season text for season 0"
              }
            ]
          },
          {
            html: "Standard",
            children: [
              {
                html: "Add episode text stroke color extra"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Fix minor typos in the Striped card documentation"
          },
          {
            html: "Create <a href=\"https://titlecardmaker.com/card_types/cascade/\" target=\"_blank\" rel=\"noopener noreferrer\">page</a> for the new Cascade card type"
          },
          {
            html: "Create <a href=\"https://titlecardmaker.com/card_types/skeleton_crew/\" target=\"_blank\" rel=\"noopener noreferrer\">page</a> for the new Skeleton Crew card type"
          },
          {
            html: "Correct label for the Calligraphy card type on the home page (was Banner)"
          },
          {
            html: "Add docs on the <b>BACKSLASH</b> format string variable"
          },
          {
            html: "Improve the Getting Started docs to have more clarity around when \"basic tasks\" (source image gathering, card creation, etc.) occur"
          },
          {
            html: "Add details on all tasks in <a href=\"https://titlecardmaker.com/user_guide/scheduler/\" target=\"_blank\" rel=\"noopener noreferrer\">the scheduler</a>"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Remove the <b>include_global_defaults</b> query parameter from the <b>GET</b> <b>/api/blueprints/export/series/{series_id}/zip</b> endpoint"
          },
          {
            html: "Create new <b>PUT</b> <b>/api/sources/series/{series_id}/upload</b> endpoint to upload any number of generic Source Images to a Series"
          },
          {
            html: "Rewrite the <b>GET</b> <b>/api/series/search</b> endpoint",
            children: [
              {
                html: "No longer accept the <b>year</b>, <b>monitored</b>, or <b>font_id</b> query parameters"
              },
              {
                html: "Only return the <b>id</b>, <b>name</b>, <b>year</b>, and <b>poster_url</b> fields in the return model"
              }
            ]
          },
          {
            html: "Create <b>GET</b> <b>/api/translate/series/{series_id}/season-titles</b> endpoint to look up season titles for a given Series on TVDb; not yet implemented on the front end"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.14.0",
    date: "November 29, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Create new Score card type",
            children: [
              {
                image: "https://titlecardmaker.com/card_types/assets/score.webp",
                width: "50%"
              }
            ]
          },
          {
            html: "Add the ability to define complex filters to the home page - for example:",
            children: [
              {
                image: "https://github.com/user-attachments/assets/06adae29-b790-40f5-948c-9b3c11a07e16",
                width: "50%"
              }
            ]
          },
          {
            html: "Various significant performance improvements",
            children: [
              {
                html: "Use reduced SQL queries in various API endpoints"
              },
              {
                html: "Default to not querying the Card and Episode counts of Series on the home page - this results in ~20x speed up of loads (in my testing)",
                children: [
                  {
                    html: "This means <i>by default</i> , the \"progress bars\" of Card creation will not be displayed on the home page"
                  },
                  {
                    html: "Add a new \"Display Counts\" button to the home page tool bar which can enable the \"old\" style if the performance impact is not important"
                  }
                ]
              },
              {
                html: "Rewrite the Template page so that the Template elements are interactive <i>much</i> sooner (~15x faster in my limited testing)",
                children: [
                  {
                    html: "Populating dropdown elements in the HTML template using JavaScript (not JQuery)"
                  },
                  {
                    html: "Only initialize the extra data tabs for Templates which are opened"
                  },
                  {
                    html: "Make all asynchronous API calls in parallel, rather than sequentially"
                  }
                ]
              },
              {
                html: "Rewrite portions of the Series page so that elements are initialized via Jinja templates, not JQuery"
              }
            ]
          },
          {
            html: "Allow specification of global card-type specific blur profiles (if blurring is enabled)"
          },
          {
            html: "Load same-Series Title Cards <i>together</i> (not separately) in Plex/Tautulli Webhook triggers for seasons and shows"
          },
          {
            html: "Add <b>TCM</b> label using batch edits in Plex"
          },
          {
            html: "Significantly improve Kometa / MediUX YAML importing:",
            children: [
              {
                html: "Download images in parallel"
              },
              {
                html: "Load cards in batches"
              }
            ]
          },
          {
            html: "Various database performance improvements:",
            children: [
              {
                html: "Add explicit column names for clean, full, and sort names (were previously hybrid properties)"
              },
              {
                html: "Add indices for sort name columns"
              },
              {
                html: "This is implemented as schema <b>2dc1e976a801</b>"
              }
            ]
          },
          {
            html: "Update to Python 3.13"
          },
          {
            html: "Display loading/progress indication for various interactions on the Series pag"
          },
          {
            html: "Allow overwriting the Image Source Priority setting in Series and Templates within the UI"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Properly utilize per-season backdrops in Card creation (pushed as hotfix)"
          },
          {
            html: "Properly fall back to the global Image Source Priority if resolved setting is blank"
          },
          {
            html: "No longer create new Templates with <i>empty</i> (not null) Image Source Priority settings"
          },
          {
            html: "Correctly display existing global card-type Fonts on the Settings page"
          },
          {
            html: "Fix uploading season logo files within the UI"
          },
          {
            html: "Return the watched Source Image details if an unwatched art style is being used <i>but</i> the Episode is watched in all assigned libraries"
          },
          {
            html: "Correctly remove the <b>Overlay</b> label from Plex if Kometa integration is enabled; this was corrected by PlexAPI <b>4.16.0</b> which fixes a bug related to batch label operations"
          },
          {
            html: "Fix individually reloading individual Cards via the UI"
          },
          {
            html: "Fix saving and applying global extras for remote card types"
          },
          {
            html: "Delete duplicate Episodes in the Clean Database task"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Remove confusing \"Found __ via Sonarr, but not in server\" log message"
          },
          {
            html: "Stop logging episodes which are not loaded in Plex card loading"
          },
          {
            html: "Add the ability to capture any generic package logging by defining the <b>TCM_PACKAGE_LOGGING</b> environment variable as a comma-separated string of package/logger names - e.g. <b>sqlalchemy,aiohttp.server</b>"
          },
          {
            html: "Improve frontend load times for Templates by initializing dropdowns in HTML directly, not via JQuery"
          },
          {
            html: "Use \"new\" style of Python <b>Union</b> and <b>Optional</b> type annotations"
          },
          {
            html: "Begin preliminary integration to optional background removal services (for in-UI mask image editing and creation)"
          },
          {
            html: "Indicate action icons as clickable on the System page"
          },
          {
            html: "Blur the page content behind all Sync modals"
          },
          {
            html: "Move the \"unmonitored series do not download source images\" warning on the Series page to the header"
          },
          {
            html: "Do not display individual \"rescheduled ___\" toasts when modifying Task schedules"
          },
          {
            html: "Include Mask Images in Blueprint exports"
          },
          {
            html: "Add generic <b>custom_field</b> extra to the variable overrides section"
          },
          {
            html: "Add <b>dict</b> as available builtin function/object in format strings"
          },
          {
            html: "Add unit labels to extras which have a unit (usually just pixels)"
          },
          {
            html: "Add a new Template filter argument for the current time - this should allow for automatically updating cards based on the time"
          },
          {
            html: "Add a Download card button to the card popup on the Series page"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Validate raw image content downloaded from MediUX before importing"
          },
          {
            html: "Handle empty (<b>null</b>) episode data and airdate returns from TVDb"
          },
          {
            html: "Create Cards which do not require a Source Image in the Plex/Tautulli webhook endpoints"
          },
          {
            html: "Improve handling of bad card settings in Card creation during webhook triggers"
          },
          {
            html: "Fix YAML setting imports for TMDb and Plex settings"
          },
          {
            html: "Begin using raw (<b>r''</b>) strings in ImageMagick command definitions to stop Python syntax warnings from displaying at runtime"
          },
          {
            html: "Use a simpler (more mobile friendly) style of \"loader\" on the home page"
          },
          {
            html: "Re-display the loader when navigating between pages of Series on the home page"
          },
          {
            html: "Correct return type for importing blank global options via the API"
          },
          {
            html: "Add placeholder text to the Series' Template dropdown"
          },
          {
            html: "Revise log edits for Episode database ID changes made on unattached Sessions (in background tasks)"
          },
          {
            html: "Properly refresh the Card interaction popup after manually refreshing the Card previews"
          },
          {
            html: "Fix suggested character replacements for <b>\\</b> when analyzing Fonts - suggest as <b>post:\\</b> so that manually-entered newline characters are not replaced"
          },
          {
            html: "Handle automatically deleted log files (due to rotation policy) when querying log files for specific text"
          },
          {
            html: "Use the same button classes for all Font actions to fix small pixel misalignment on the Transfer Font buttons"
          },
          {
            html: "Use improved Episode equality comparison logic which allows for matching on the absolute episode numbers"
          },
          {
            html: "v1 Fix default frame color for Tinted Frame cards made with the mini maker"
          },
          {
            html: "v1 Add <b>--debug</b> flag to the mini maker card creation to print the ImageMagick command history"
          },
          {
            html: "v1 Improve error logging for non-async runs of TCM"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Create Score card type"
          },
          {
            html: "Anime",
            children: [
              {
                html: "Increase the default kerning of all kanji - this was erroneously changed in a prior version from <b>2</b> to <b>-3</b>, this reverts this"
              }
            ]
          },
          {
            html: "Banner",
            children: [
              {
                html: "Limit the banner height between 0 and 1800 pixels"
              },
              {
                html: "Limit the text offset between 0 and 3200 pixels"
              },
              {
                html: "Rename the \"Banner Toggle\" extra to \"Disable Banner\""
              }
            ]
          },
          {
            html: "Banner",
            children: [
              {
                html: "Add new episode text box fill color extra"
              }
            ]
          },
          {
            html: "Landscape",
            children: [
              {
                html: "Add new darken color extra"
              }
            ]
          },
          {
            html: "Notification",
            children: [
              {
                html: "v1 Change the default separator character for cards made with the mini maker"
              }
            ]
          },
          {
            html: "Shape",
            children: [
              {
                html: "Fix typo in an extra description"
              }
            ]
          },
          {
            html: "Star Wars",
            children: [
              {
                html: "Add support for custom Font kerning adjustements"
              }
            ]
          },
          {
            html: "Striped",
            children: [
              {
                html: "Add episode text vertical shift extra"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Add new horizontal shift extras to adjust the title and index/episode text"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Various Getting Started page improvements:",
            children: [
              {
                html: "Remove outdated reference to Template filters"
              },
              {
                html: "Fix typo for an icon on the scheduler page"
              },
              {
                html: "Add a step to the Docker instructions to check the volume mounts are working correctly to prevent accidental data loss"
              },
              {
                html: "Remove <b>docker run</b> command breakdown to avoid confusion"
              },
              {
                html: "Remove the outdated link to the Tautulli Connection setup, as this is now linked on the Plex page"
              }
            ]
          },
          {
            html: "Add documentation on the global settings for default templates, global fonts, global extras, and default blur profiles"
          },
          {
            html: "Finish various card type pages:",
            children: [
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/anime/\" target=\"_blank\" rel=\"noopener noreferrer\">Anime</a>"
              },
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/banner/\" target=\"_blank\" rel=\"noopener noreferrer\">Banner</a>"
              },
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/calligraphy/\" target=\"_blank\" rel=\"noopener noreferrer\">Calligraphy</a>"
              },
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/score/\" target=\"_blank\" rel=\"noopener noreferrer\">Score</a>"
              },
              {
                html: "<a href=\"https://titlecardmaker.com/card_types/white_border/\" target=\"_blank\" rel=\"noopener noreferrer\">White Border</a>"
              }
            ]
          },
          {
            html: "Document global \"Delete Un-Synced Series\" setting"
          },
          {
            html: "Move global \"Source Image Deletion\" setting into appropriate section of the Settings page"
          },
          {
            html: "v1 Minor improvements to the sync documentation examples"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Add query parameter on whether to refresh all episode IDs in the <b>POST</b> <b>/api/episodes/series/{series_id}/refresh</b> endpoint"
          },
          {
            html: "Create API endpoints for managing mask images",
            children: [
              {
                html: "<b>PUT</b> <b>/api/sources/episode/{episode_id}/mask</b> to upload a mask to a given Episode"
              },
              {
                html: "<b>DELETE</b> <b>/api/sources/episode/{episode_id}/mask</b> to delete a mask for a given Episode"
              }
            ]
          },
          {
            html: "Modify return schema of <b>GET</b> <b>/api/series/all</b> - see new API specification for details"
          },
          {
            html: "Create new <b>GET</b> <b>/api/series/all-extended</b> endpoint to function <i>like</i> the old <b>/api/series/all</b> endpoint"
          },
          {
            html: "Create a new <b>GET</b> <b>/api/cards/series/{series_id}/reduced</b> endpoint to return a reduced Card model which does not contain the JSON definition"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.13.0",
    date: "November 01, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Create new Negative Space card type",
            children: [
              {
                html: "All documentation is available <a href=\"https://titlecardmaker.com/card_types/negative_space/\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>",
                children: [
                  {
                    image: "https://titlecardmaker.com/card_types/assets/negative_space.webp",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Add toggle for using season-specific assets (logos and backdrops) for Series",
            children: [
              {
                html: "Once enabled, TCM will allow directly setting logos and backdrops for each season within the UI"
              },
              {
                html: "Requires SQL schema <b>a1520b6160c4</b>"
              }
            ]
          },
          {
            html: "Add per-Series and per-Template level Image Source Priority customization",
            children: [
              {
                html: "Requires SQL schema <b>a1520b6160c4</b>"
              }
            ]
          },
          {
            html: "Display the Series name in Blueprints which are a part of a Set while on the Series page"
          },
          {
            html: "Add the ability to \"intercept\" Plex API logging and route all messages to the TCM logging mechanism by setting the environment variable <b>TCM_PLEX_LOGGING</b> to <b>TRUE</b>"
          },
          {
            html: "Remove all references to the \"blacklist\" from TMDb"
          },
          {
            html: "Add the ability to delete Source Images from the UI"
          },
          {
            html: "Add pop-up image interactions to Title Cards and Source Images within the UI",
            children: [
              {
                html: "Previously, clicking a Source Image would launch the browser; now a popup is shown",
                children: [
                  {
                    image: "https://github.com/user-attachments/assets/97b87048-83a3-442e-b5e9-ce6174def99b",
                    width: "20%"
                  }
                ]
              },
              {
                html: "Previously, clicking or right-clicking a Title Card would create the Card (if globally enabled); now a popup is shown",
                children: [
                  {
                    image: "https://github.com/user-attachments/assets/7f3030a8-3748-459a-a5e1-0e0445edb84e",
                    width: "20%"
                  }
                ]
              },
              {
                html: "Add the ability to selectively load any Title Card into any Connection/library/episode"
              },
              {
                html: "Remove the checkmark over Title Cards which indicated whether a Title Card is loaded or not - this is now shown in the popup"
              }
            ]
          },
          {
            html: "Minor improvements to the Plex Webhook",
            children: [
              {
                html: "Run in a separate asynchronous thread so that the UI does not lock up while processing"
              },
              {
                html: "Add <b>timeout</b> query parameter to stop the webhook if it takes longer than the specified number of seconds (defaults to 120)"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Properly implement restoring from backups via the UI / API"
          },
          {
            html: "Only reload Cards if a Card config actually changed when triggered via a Plex Webhook"
          },
          {
            html: "Correct SQL model reference used to import a Series and Blueprint"
          },
          {
            html: "Handle bad remote card type JSON loading while launching the UI - remote card types will now just be skipped, not result in the UI failing to load"
          },
          {
            html: "Fix setting the global card extension to <b>.jxl</b> via the UI"
          },
          {
            html: "Correctly apply minimum Source Image resolution settings for TVDB Connections"
          },
          {
            html: "Pin the <b>cryptography</b> package version to <b>42.0.8</b> for ARMv7 Docker images"
          },
          {
            html: "Fix resetting Episode extras via the UI"
          },
          {
            html: "Properly handle deleting old database ID's which did not exist in the <b>SetSeriesIDs</b> task"
          },
          {
            html: "Properly download logos from TVDb (was downloading posters)"
          },
          {
            html: "Handle changing season/episode/absolute numbers when refreshing episode data"
          },
          {
            html: "Properly batch label removal when loading Cards into Plex"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add an icon to directly perform a system backup via the System page"
          },
          {
            html: "Fix and improve various E2E tests"
          },
          {
            html: "Change the log level of various messages to be less annoying"
          },
          {
            html: "Remove the ability to display Source Image information in non-tabular form"
          },
          {
            html: "Move the edit poster dialog into a popup menu rather than a modal"
          },
          {
            html: "Move the home page table/poster toggle button to the right side of the menu bar"
          },
          {
            html: "Move all Series \"delete\" functionalities (delete Title Cards, Series, etc.) to a separate submenu"
          },
          {
            html: "Update all package dependency versions"
          },
          {
            html: "Add the ability to adjust the minimum log message level of the live log messages with the <b>TCM_LOG_WEBSOCKET</b> environment variable"
          },
          {
            html: "Remove the \"search\" Source Image interaction/column from the UI - this was confusing for most users, and rarely useful"
          },
          {
            html: "No longer auto refresh Card previews on the Series page"
          },
          {
            html: "Add ability to delete Source Images from the UI"
          },
          {
            html: "Only set Episode IDs for <i>new</i> Episodes when refreshing episode data"
          },
          {
            html: "Display a Connection's available libraries within the UI on the Connections page"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Properly display the browse asset button(s) within the UI if TMDb is disabled"
          },
          {
            html: "Improve handling of bad image content in logo and backdrop upload endpoints"
          },
          {
            html: "Reject series without premiere years in Jellyfin when querying Series IDs"
          },
          {
            html: "Handle all generic exceptions when parsing Plex webhooks - most commonly <b>ClientDisconnent</b> errors"
          },
          {
            html: "Improve parsing of log messages without valid datetimes"
          },
          {
            html: "Correct handling of logging bad poster URL uploads in Plex"
          },
          {
            html: "Raise 422 if the specified Connection in a <b>/api/proxy</b> API call does not have a defined URL"
          },
          {
            html: "Display generic \"Some time ago\" text if the time difference cannot be determined for log messages on the Series page"
          },
          {
            html: "Correctly display a success message when a Title Card is deleted in the UI"
          },
          {
            html: "Do not raise an exception if a specified interface does not exist when downloading logos for a Series"
          },
          {
            html: "Do not reset currently running Tasks when initializing the Scheduler"
          },
          {
            html: "Properly show an error toast when TMDb returns no posters when querying via the UI"
          },
          {
            html: "Add scrolling for x-overflow on the Logs page"
          },
          {
            html: "v1 Do not include unique source images in the missing file report if both styles are art"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Cutout",
            children: [
              {
                html: "Add extra to shift the vertical position of the cutout text"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Improve the \"how to update\" docs to reference <b>docker pull</b> command for non-compose Docker setups"
          },
          {
            html: "Improve documentation for <a href=\"https://titlecardmaker.com/user_guide/#environment-variables\" target=\"_blank\" rel=\"noopener noreferrer\">environment variables</a>"
          },
          {
            html: "Write documentation on the \"live log messages\" and \"interactive title card\" global settings <a href=\"https://titlecardmaker.com/user_guide/settings/\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Fix <b>/api/connections/tautulli/check</b> endpoint"
          },
          {
            html: "Sleep for only 15 seconds between polling for Episodes in the Sonarr webhook endpoint"
          },
          {
            html: "Change the default page size of all paginated endpoints to 50 (from 100)"
          },
          {
            html: "Fix return model for <b>POST</b> <b>/api/sources/episode/{episode_id}</b> if any image source returns a null image"
          },
          {
            html: "Add <b>season_number</b> query parameter to various API endpoints",
            children: [
              {
                html: "<b>PUT</b> <b>/api/sources/series/{series_id}/logo/upload</b>"
              },
              {
                html: "<b>PUT</b> <b>/api/sources/series/{series_id}/backdrop/upload</b>"
              }
            ]
          },
          {
            html: "Raise <b>422</b> if the <b>interface_id</b> query parameter passed in <b>DELETE</b> <b>/api/series/series/{series_id}/plex-labels/library</b> endpoint does not correspond to a valid Plex Connection"
          },
          {
            html: "Create new API endpoint to delete a Series (or season) logo or backdrop - <b>DELETE</b> <b>/api/sources/series/{series_id}/logo</b> and <b>DELETE</b> <b>/api/sources/series/{series_id}/backdrop</b>"
          },
          {
            html: "Change <b>PUT</b> <b>/api/series/series/{series_id}/poster</b> Form argument names from <b>poster_url</b> and <b>poster_file</b> to <b>url</b> and <b>file</b>"
          },
          {
            html: "Rewrite the Card loading API endpoints",
            children: [
              {
                html: "Deprecate <b>PUT</b> <b>/api/cards/series/{series_id}/load/all</b>"
              },
              {
                html: "Deprecate <b>PUT</b> <b>/api/cards/series/{series_id}/load/library</b>"
              },
              {
                html: "Create new <b>PUT</b> <b>/api/cards/series/{series_id}/load</b> endpoint which optionally takes <b>interface_id</b> and <b>library_name</b> query parameters"
              }
            ]
          },
          {
            html: "Create new <b>PUT</b> <b>/api/cards/episode/{episode_id}/load</b> endpoint to load the Title Cards for a single Episode"
          },
          {
            html: "Add <b>timeout</b> query parameter to <b>POST</b> <b>/api/webhooks/plex</b>"
          },
          {
            html: "Create <b>PUT</b> <b>/api/cards/card/{card_id}/load</b> endpoint to reload a Card"
          },
          {
            html: "Create <b>GET</b> <b>/api/episodes/series/{series_id}/connection/{interface_id}/</b> endpoint to query remote episode data on a given Connection"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.12.1",
    date: "September 22, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Display whether a Card has been loaded into at least one media server within the UI - loaded cards will have a small green check mark in the top-left corner"
          },
          {
            html: "Add the ability to globally change the default Font settings used by each card type"
          },
          {
            html: "Add in-UI support for restoring from or deleting system backups"
          },
          {
            html: "Only process <i>new</i> Episodes when new content triggers TCM via the Plex Webhook"
          },
          {
            html: "Download imported Cards as Cards <i>and</i> Source Images when importing as \"textless\" in the Kometa / MediUX import"
          },
          {
            html: "Add a list of Series which are missing logos to the Missing page"
          },
          {
            html: "Add ability to transfer all references from an existing Font to another existing Font"
          },
          {
            html: "Make slight changes to the Plex Webhook integration",
            children: [
              {
                html: "Add the <b>require_owner</b> query parameter to the Plex Webhook endpoint"
              },
              {
                html: "Change the <b>trigger_on</b> query parameter of the Plex Webhook endpoint to default to <b>library.new,media.scrobble</b> with no builtin defaults"
              }
            ]
          },
          {
            html: "Rotate log files every 10 MB (from 25 MB) to reflect Discord's new non-Nitro file size limit"
          },
          {
            html: "Add new global UI settings for the page size/dimension settings of Title Cards and Source Images displayed on the Series page"
          },
          {
            html: "Perform batch API operations when loading Cards into Plex - this should be a significant speed / stability improvement (especially when loading lots of Cards)"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Properly load remote card types if set as the global card type when not assigned to an existing Template/Series/Episode"
          },
          {
            html: "Properly delete <i>all</i> Font files in the Font asset directory when deleting files via the API"
          },
          {
            html: "Delete and replace any existing Font files when uploading a new Font via the API"
          },
          {
            html: "Do not process Kometa / MediUX Card imports in the main event loop (effectively freezing the UI)"
          },
          {
            html: "Do not limit the overflow pool of database connections"
          },
          {
            html: "Pin <b>fastapi</b> package version to <b>0.112.2</b> to fix the <b>fastapi-pagination</b> bug for new parameter names"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Also redact host-only URLs in logs - e.g. for <b>http://192.168.0.1:8989</b>, redact <b>http://192.168.0.1</b> <i>and</i> the full URL"
          },
          {
            html: "Add easy copy-paste functionality to some elements of the System page"
          },
          {
            html: "Remove the current version label from the bottom of the Settings page - this is now only on the System page"
          },
          {
            html: "Properly commit translation changes when creating Cards in a background task"
          },
          {
            html: "Remove deleted Template element from the page without re-querying all Templates when deleting via the UI"
          },
          {
            html: "Add new \"file does not exist\" Template filter condition"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Properly handle database backups with no alembic version table in parsing"
          },
          {
            html: "Catch Plex API exceptions raised while adding labels to Plex uploads"
          },
          {
            html: "Remove sort interaction for restore and delete columns on the backups table"
          },
          {
            html: "Skip internal server errors with invalid log timestamps"
          },
          {
            html: "Pin the Starlette package version to <b>0.38.4</b> to avoid race conditions caused by multiple middlewares"
          },
          {
            html: "Fix \"false\" default values in some alembic SQL schema migrations which were erroneously set to \"true\""
          },
          {
            html: "Handle floating point imprecision for some font percentages (size/kerning/stroke width) when displayed in the UI"
          },
          {
            html: "Do not stack <b>onclick</b> events when launching the same edit Sync modal repeatedly"
          },
          {
            html: "Correctly handle a non-existent User when editing credentials via the API"
          },
          {
            html: "Fix interface-specific library availability API endpoints"
          },
          {
            html: "v1 Properly load any local <b>.env</b> file when launching the mini maker"
          },
          {
            html: "Properly parse pre-initialization log messages which do not use the default timezone"
          },
          {
            html: "Improve handling of invalid <b>SplitCharacteristics</b> properties in custom card type classes"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "v1 Fix custom archive determination for configs using a custom <b>episode_text_color</b>"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Allow the Episode Text Font Size extra to go to <b>0.0</b>"
              },
              {
                html: "Allow the Frame Width extra to go to <b>0</b>"
              },
              {
                html: "Limit the Frame Width extra to a maximum of <b>1600</b> pixels"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Update Plex webhook documentation to reflect changes to the new <b>trigger_on</b> parameter"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Create new <b>/missing</b> API router",
            children: [
              {
                html: "Create <b>GET</b> <b>/api/missing/cards</b> endpoint to get details of all Episodes without Cards"
              },
              {
                html: "Create <b>GET</b> <b>/api/missing/logos</b> endpoint to get details of all Series without logo files"
              },
              {
                html: "Deprecate <b>GET</b> <b>/api/cards/missing</b> endpoint"
              }
            ]
          },
          {
            html: "Add the <b>require_owner</b> query parameter to the Plex Webhook endpoint"
          },
          {
            html: "Change the <b>trigger_on</b> query parameter of the Plex Webhook endpoint to default to <b>library.new,media.scrobble</b> (with no builtin defaults)"
          },
          {
            html: "Create <b>/backups</b> API router",
            children: [
              {
                html: "Move all backup related API endpoints to this subrouter"
              },
              {
                html: "Deprecate <b>GET</b> <b>/api/settings/backups</b> - new endpoint is <b>GET</b> <b>/api/backups/all</b>"
              }
            ]
          },
          {
            html: "Raise <b>409</b> HTTP code if there is no globally assigned Episode Data Source when refreshing data for a Series"
          },
          {
            html: "Do not return any content from the <b>POST</b> <b>/api/backups/backup</b> endpoint"
          },
          {
            html: "Remove previously deprecated endpoints:",
            children: [
              {
                html: "<b>POST</b> <b>/api/scheduler/type/{mode}</b>"
              },
              {
                html: "<b>POST</b> <b>/api/series/sonarr/delete</b>"
              },
              {
                html: "<b>POST</b> <b>/api/cards/key</b>"
              },
              {
                html: "<b>POST</b> <b>/api/cards/sonarr</b>"
              },
              {
                html: "<b>GET</b> <b>/api/statistics/</b>"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.12.0",
    date: "August 27, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "<i>BREAKING CHANGE</i> - No longer use <b>pipenv</b> for non-Docker Python dependency virtual environment management",
            children: [
              {
                html: "Use <a href=\"https://docs.astral.sh/uv/\" target=\"_blank\" rel=\"noopener noreferrer\">uv</a> instead"
              },
              {
                html: "This is ~10-100x faster than Pipenv"
              },
              {
                html: "Has built-in support for multiple Python versions and on-the-fly Python installation"
              },
              {
                html: "All documentation has been updated, but old <b>pipenv run</b> commands can be replaced with <b>uv run</b> (after installation)"
              }
            ]
          },
          {
            html: "Added support for Plex Webhooks",
            children: [
              {
                html: "Here is a real-time example of Plex triggering TCM to create a new Card on item <i>rating</i> :",
                children: [
                  {
                    image: "https://github.com/user-attachments/assets/4ef65968-cef5-43f7-8aa5-cb209f61ecb0",
                    width: "50%"
                  }
                ]
              },
              {
                html: "Documentation to implement these is available <a href=\"https://titlecardmaker.com/user_guide/integrations/#plex\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
              },
              {
                html: "These are the preferred method of triggering fast-updates from Plex (instead of Tautulli), as they are much faster and allow support for custom conditions"
              }
            ]
          },
          {
            html: "Add real-time log messages to the UI (and no longer poll logs on fixed interval)",
            children: [
              {
                html: "These messages will appear in the lower right corner of the UI"
              },
              {
                html: "Messages are sent via WebSockets, so users who have disabled these via a proxy will need to remove that if you want these messages"
              },
              {
                html: "Add global option \"Disable Live Log Messages\" which can be toggled if you do not want these"
              }
            ]
          },
          {
            html: "Reorganize part of the sidebar",
            children: [
              {
                html: "Create new \"System\" page which contains high-level system info like the current version, database schema, server uptime, and available system backups"
              },
              {
                html: "Move the Logs, Graph, and Changelog pages under the new System menu"
              },
              {
                html: "Change the menu icon for the Settings page"
              }
            ]
          },
          {
            html: "Merge two new user-submitted card types:",
            children: [
              {
                html: "The <b>Supremicus/Dawn</b> card, created by Supremicus",
                children: [
                  {
                    image: "https://raw.githubusercontent.com/Supremicus/tcm-images/main/Preview%20Cards/DawnTitleCard.preview.jpg",
                    width: "50%"
                  }
                ]
              },
              {
                html: "The <b>Supremicus/Horizon</b> card, also created by Supremicus",
                children: [
                  {
                    image: "https://raw.githubusercontent.com/Supremicus/tcm-images/main/Preview%20Cards/HorizonTitleCard.preview.jpg",
                    width: "50%"
                  }
                ]
              },
              {
                html: "Both of these cards are very thorough and can be fine-tuned quite a bit. I recommend reading their extras and perhaps the <a href=\"https://github.com/CollinHeist/TitleCardMaker-CardTypes/tree/web-ui/Supremicus\" target=\"_blank\" rel=\"noopener noreferrer\">README</a> if you are interested"
              }
            ]
          },
          {
            html: "Significantly improve Docker build times - <i>_huge_</i> thanks to mchangrh for developing these"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix series ID replacement in Emby and Jellyfin"
          },
          {
            html: "Fix downloading Source Images from Plex via the UI"
          },
          {
            html: "Fix setting Emby series ID's for Series without ID's"
          },
          {
            html: "Fix Syncing from Emby when no filter libraries are indicated"
          },
          {
            html: "Fix querying Series ID's from Emby on some servers"
          },
          {
            html: "Correct the crontab schedule of the \"Clean Database\" Task when the Scheduler is in advanced mode"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add new Sync setting to automatically mark all added Series as Unmonitored",
            children: [
              {
                html: "This setting can be toggled if you want to fine-tune which Series have Cards created for them (but don't want to use a more fine-tuned Sync filter)"
              },
              {
                html: "Requires schema revision <b>db6a1eda7d21</b>"
              }
            ]
          },
          {
            html: "Add a list of internal server errors to the Logs page",
            children: [
              {
                html: "These will appear at the bottom of the Logs page, and can be clicked to easily open an Issue on the GitHub for this error"
              }
            ]
          },
          {
            html: "Log the file name of uploaded files when uploading Cards to Plex"
          },
          {
            html: "v1 Add series characteristics to card initialization"
          },
          {
            html: "v1 Delete (do not reset) extras in Music and Standard card type archive sub-variations"
          },
          {
            html: "Cache parsed log data for all inactive log files - this will significantly speed up log loading and searching"
          },
          {
            html: "Add loading placeholders to the home page statistics (in place of the X"
          },
          {
            html: "Add the log message's context ID to the right-side of the log message on the Series page"
          },
          {
            html: "Remove the CSS max content width from log messages on the Series page"
          },
          {
            html: "v1 Add the <b>abs_episode_number</b> variable to card initialization"
          },
          {
            html: "Reduce the active menu icon glow by 2px"
          },
          {
            html: "Rewrite the mini maker script to use improved sub-command syntax - e.g. <b>mini_maker.py genre-card {...}</b>"
          },
          {
            html: "Add placeholder text to the name fields when creating Syncs"
          },
          {
            html: "v1 Add <b>--font-vertical-shift</b> arguments to the mini maker for season and movie posters"
          },
          {
            html: "Use Background Tasks in the Episode data refresh API endpoint"
          },
          {
            html: "Add support for additional card extensions - namely <b>.avif</b>, <b>.heic</b>, and <b>.jxl</b>"
          },
          {
            html: "Remove support for the <b>.gif</b> card extension"
          },
          {
            html: "Remove explicit <b>poetry</b> version management files, move to <b>uv</b>"
          },
          {
            html: "Exclude <b>sqlalchemy</b> code from logged tracebacks"
          },
          {
            html: "Include JQuery file directly, do not load via CDN"
          },
          {
            html: "Utilize new SQL DB connections for functions executed in Background Tasks",
            children: [
              {
                html: "As of FastAPI v0.106.0, yielded dependencies do not persist after the request response has been sent, so this requires new DB connections to be made for each background function"
              }
            ]
          },
          {
            html: "Reorganize the Connections forms to use two columns of inputs, rather than one"
          },
          {
            html: "Only make up to five attempts when loading single-Episode Cards (via API) to <i>Plex</i> , not Emby or Jellyfin"
          },
          {
            html: "Create new Sonarr integration/webhook to add Series to TCM as they're added to Sonarr; this has marginal benefit over Syncing, but is available regardless - see <a href=\"https://titlecardmaker.com/user_guide/integrations/#__tabbed_1_1\" target=\"_blank\" rel=\"noopener noreferrer\">here</a> for details"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Use <b>web-ui</b> branch for all user card type file and cards"
          },
          {
            html: "Do not reset the <b>days</b> URL query parameter when loading the Graphs page"
          },
          {
            html: "v1 Add the <b>backdrop_file</b> argument to Title Card initialization"
          },
          {
            html: "Fix the \"... days ago\" text which could appear within the UI as <i>literally</i> <b>diffDays days</b>"
          },
          {
            html: "Improve rich formatting when searching log message for multiple <b>|</b>-separated values"
          },
          {
            html: "Do not attempt to query the ImageMagick prefix when executing in Docker mode"
          },
          {
            html: "v1 Utilize improved Jellyfin Series matching with database ID's"
          },
          {
            html: "Reword the \"Run this Task\" text which appears on the Scheduler page"
          },
          {
            html: "Do not refresh Episode data when a Series is newly added <i>if</i> it was added as Unmonitored"
          },
          {
            html: "v1 Improve handling of Episodes without indices when querying watched statuses from Jellyfin"
          },
          {
            html: "Detect bad images from TPDb uploaded via the API"
          },
          {
            html: "Detect all types of bad images uploaded via the poster upload API endpoint"
          },
          {
            html: "Improve handling of Jellyfin episodes without a defined ProviderId field"
          },
          {
            html: "Improve handling of Jellyfin episodes without titles"
          },
          {
            html: "Pin <b>rich</b> package version to <b>13.8.0</b> to use my PR'd fixes which were causing an \"internal server error\" during some traceback logging"
          },
          {
            html: "Potentially fix AJAX-blocked statistics query on the home page for some users using reverse proxies"
          },
          {
            html: "Also redact host-only URLs from logs - e.g. for <b>192.168.0.29:32400</b>, redact just <b>192.168.0.29</b>"
          },
          {
            html: "Handle exceptions raised while adding the TCM label to objects while loading images into Plex"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Add season text color extra (defaults to matching the episode text color)"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Add documentation on selecting a branch or Docker tag <a href=\"https://titlecardmaker.com/user_guide/\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
          },
          {
            html: "Add documentation on all available environment variables <a href=\"https://titlecardmaker.com/user_guide/#environment-variables\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
          },
          {
            html: "Add a note about which Connection fields are encrypted within TCM to the Connection page docs"
          },
          {
            html: "Create <a href=\"https://titlecardmaker.com/user_guide/system/\" target=\"_blank\" rel=\"noopener noreferrer\">System Summary</a> User Guide page"
          },
          {
            html: "Use new preview image(s) for the Logs page"
          },
          {
            html: "Describe the log files and internal server errors section of the Logs page"
          },
          {
            html: "Document all webhook <a href=\"https://titlecardmaker.com/user_guide/integrations/\" target=\"_blank\" rel=\"noopener noreferrer\">integrations</a> in the User Guide"
          },
          {
            html: "Add documentation on the TVDb Connection to the User Guide"
          },
          {
            html: "No longer recommend Tautulli, instead prefer Plex Webhooks"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Add <b>exists()</b> method to the <b>RemoteFile</b> class - can be used in remote card types"
          },
          {
            html: "Create <b>GET</b> <b>/api/logs/errors</b> endpoint to get all internal server errors which appear in log files"
          },
          {
            html: "Create <b>GET</b> <b>/api/logs/files/{filename}/zip</b> endpoint to get a .zip version of a given log file"
          },
          {
            html: "Add the <b>previous_hours</b> query parameter to the <b>GET</b> <b>/api/statistics/snapshots</b> endpoint"
          },
          {
            html: "Create <b>GET</b> <b>/api/settings/background-tasks</b> endpoint to view all pending Background Task information",
            children: [
              {
                html: "This currently just returns the pending function name and docstring; this will be changed"
              }
            ]
          },
          {
            html: "Change the HTTP method for explicitly setting the scheduler mode (<b>/api/scheduler/type/{mode}</b>) - <b>POST</b> has been deprecated, new method is <b>PUT</b>"
          },
          {
            html: "Add <b>snapshot</b> query parameter to <b>/api/webhooks/plex/rating-key</b> endpoint"
          },
          {
            html: "Reorganize all Webhook-related endpoints into a separate <b>/webhooks/</b> router",
            children: [
              {
                html: "Deprecate <b>POST</b> <b>/api/series/sonarr/delete</b> - new route is <b>/api/webhooks/sonarr/series/delete</b>"
              },
              {
                html: "Deprecate <b>POST</b> <b>/api/cards/key</b> - new route is <b>/api/webhooks/plex/rating-key</b>"
              },
              {
                html: "Deprecate <b>POST</b> <b>/api/cards/sonarr</b> - new route is <b>/api/webhooks/sonarr/cards</b>"
              }
            ]
          },
          {
            html: "Fix <b>GET</b> <b>/api/available/version</b> and <b>GET</b> <b>/api/settings/version</b> endpoints"
          },
          {
            html: "Deprecate <b>GET</b> <b>/api/statistics/</b> endpoint - new route is <b>/api/statistics/system</b>"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.11.0",
    date: "July 21, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Begin implementing automated front-end testing with <a href=\"https://www.cypress.io/\" target=\"_blank\" rel=\"noopener noreferrer\">Cypress</a>"
          },
          {
            html: "Allow importing series poster, series backgrounds, and season posters via Kometa / MediUX YAML (this works for Emby, Jellyfin, and Plex)"
          },
          {
            html: "Add ability to delete all Series which are not a part of <i>any</i> Sync",
            children: [
              {
                html: "Adds a global setting called \"Delete Un-Synced Series\" on the Settings page"
              },
              {
                html: "If enabled, TCM will delete the Series, Cards, and Source Images (if enabled) of any Series which is not included in any Sync"
              },
              {
                html: "<b>This is a potentially destructive setting</b> - be careful before enabling. Deleted Cards and Source Images are not backed up by TCM"
              }
            ]
          },
          {
            html: "Add global option for the ImageMagick executable path",
            children: [
              {
                html: "This option replaces the <b>TCM_IM_PATH</b> environment variable"
              },
              {
                html: "This setting is only applicable to <i>some</i> Windows users"
              }
            ]
          },
          {
            html: "Significantly improve front-end error messages for Title Card validation failures - TCM will now display more \"human readable\" messages of the specific field validations which caused the creation to fail"
          },
          {
            html: "Reorganize the Templates page",
            children: [
              {
                html: "Move the preview cards to the top of the template (from the side) to allow the options to take up the full width of the page"
              },
              {
                html: "Display extras in groups of three fields, not two"
              },
              {
                html: "Join some input fields together"
              }
            ]
          },
          {
            html: "Remove the \"Delete Missing\" option for named Fonts - this was rarely used, not well documented, and largely superfluous"
          },
          {
            html: "Add the TCM version number to backup filenames"
          },
          {
            html: "Rotate logs every 12 hours <i>or</i> every 24.9 Megabytes (was just every 12 hours) in order to prevent logs from exceeding the default Discord upload size limit"
          },
          {
            html: "Various security improvements",
            children: [
              {
                html: "Generate a random encryption key <i>on-device</i> at boot time for TCM, rather than using hard-coded value"
              },
              {
                html: "Encrypt all private Connection details (URLs and API keys) within the database, rather than keep them in plaintext"
              },
              {
                html: "Do not send private Connection details in API responses even if the user is authorized"
              },
              {
                html: "Properly redact secrets which may appear in exception tracebacks - this most commonly occurred in Plex API errors which include the X-Plex-Token as a header parameter"
              },
              {
                html: "Redact secrets in order of descending length to prevent possible \"leaking\" partial substrings of the secret if contained in another secret - e.g. if you had an API key of <b>ABC</b> and <b>ABCDEF</b>, previously <b>ABC</b> could have been redacted <i>first</i> , resulting in <b>DEF</b> kept as-is in the logs"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix handling of dynamic Emby and Jellyfin database ID's",
            children: [
              {
                html: "Series are now searched for <i>without</i> the year if not found by year (only applicable to Jellyfin)"
              },
              {
                html: "Match Series by database ID's, not just name"
              },
              {
                html: "Dynamically validate and update Series ID's to handle database changes"
              },
              {
                html: "Update and overwrite existing Series Emby and Jellyfin ID's if newer ID's are found during the Set Series ID's Task"
              }
            ]
          },
          {
            html: "Catch and handle errors raised by invalid card type models during Card imports"
          },
          {
            html: "Display the currently running Sync on Sync page (re)load"
          },
          {
            html: "Prevent multiple Syncs from being run concurrently via the UI"
          },
          {
            html: "Fix Card importing via File upload"
          },
          {
            html: "Properly initialize the Kometa integration checkbox (if enabled) within the UI"
          },
          {
            html: "Properly detect invalid TVDb API keys (and mark the Connection as invalid and disabled)"
          },
          {
            html: "Use improved full-length traceback logging in log <i>files</i> , not just stdout"
          },
          {
            html: "Fix Source Image gathering if TVDb is a specified source <i>and</i> has no images"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add sidebar link to the Changelog (accessible from the Settings submenu)"
          },
          {
            html: "Minor QOL improvements for extra inputs",
            children: [
              {
                html: "Display the default value in the input's placeholder text"
              },
              {
                html: "Add live color bubbles to all color extra fields"
              }
            ]
          },
          {
            html: "Add some QOL visual improvements to the Logs page",
            children: [
              {
                html: "Add dynamic links for Series, Fonts, Templates, etc. when detected in log messages - e.g. a message mentioning Series 1 will include a link to the page for Series 1"
              },
              {
                html: "Highlight matching text when filtering logs by the message"
              },
              {
                html: "Significantly improve the format of traceback / error messages so they are much easier to read within the UI"
              },
              {
                html: "Add minor formatting for redacted messages"
              }
            ]
          },
          {
            html: "Reorganize the Settings page - this is just an aesthetic change to improve logical layout of various settings"
          },
          {
            html: "Pass the active user into the Connections page via Jinja2 template variable, not an API call - this will prevent page unresponsiveness if the authentication section is interacted with immediately after loading the page"
          },
          {
            html: "Improve logging when parsing invalid Kometa YAML during Card imports"
          },
          {
            html: "Print the ImageMagick command history if preview card creation fails"
          },
          {
            html: "Improve ImageMagick <b>magick</b> command prefix detection during boot - TCM will now look at what prefix should be used in background and foreground threads (was just foreground)"
          },
          {
            html: "Rename the \"Mutli Library Filename Support\" setting - now called \"Multi-Library File Naming\""
          },
          {
            html: "Log how many Series are returned from a Sync when run"
          },
          {
            html: "Remove unused <b>full_match_name</b> and <b>full_clean_name</b> attributes from <b>SeriesInfo</b> objects"
          },
          {
            html: "Add in-UI warning to verify Sonarr libraries <i>before</i> changing them"
          },
          {
            html: "Group Fonts into sub-groups if there are more than 19 Fonts per section - e.g. if there are 20 fonts that start with <b>A</b>, then it will be broken into <b>Aa</b>, <b>Ab</b>, etc."
          },
          {
            html: "Remove the Episode image source attempt counter column from the SQL database"
          },
          {
            html: "Initialize the Connections page with Jinja2 template variables, not API calls"
          },
          {
            html: "Modify logging environment variables",
            children: [
              {
                html: "<b>TCM_LOG_STDOUT</b> replaces <b>TCM_LOG</b> and adjusts the log level for the std (terminal) output"
              },
              {
                html: "Add <b>TCM_LOG_FILE</b> to change the log level for file logging - default is <b>TRACE</b>"
              },
              {
                html: "Add <b>TCM_LOG_RETENTION</b> to change how long logs are kept - default is <b>7 days</b>"
              }
            ]
          },
          {
            html: "Add the HTTP status code and text to API request terminations - e.g. <b>200 OK</b>"
          },
          {
            html: "Display logos from TMDb in \"order\" sorted by language and resolution"
          },
          {
            html: "Add right-click interactivity to Series in the home page tablular view (i.e. open in new tab)"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Pin Pydantic dependency version to <b>1.10.17</b> to fix uvicorn server launch on Python 3.12.4"
          },
          {
            html: "Use alternate randomized filenames for files downloaded during Kometa YAML parsing"
          },
          {
            html: "Reset intervals to <i>exactly</i> 10 minutes if scheduled interval is too short (was resetting only the minutes field)"
          },
          {
            html: "v1 Handle incorrectly written/formatted series record database version files"
          },
          {
            html: "Correctly initialize the card quality slider color based on the currently selected value"
          },
          {
            html: "Delay running Syncs by up to 5 minutes if a Sync is already running when the Task is executed"
          },
          {
            html: "Recursively delete <i>all</i> content in Series source folders instead of just files (if globally enabled)"
          },
          {
            html: "Handle objects specified without template ID's in the Episode card preview API endpoint"
          },
          {
            html: "Improve handling of log messages without context ID's in the log message table",
            children: [
              {
                html: "No longer add <b>null</b> to the context ID filter list when the blank cells are clicked"
              },
              {
                html: "Do not allow blank context ID cells to be clicked (also remove tool tip text)"
              }
            ]
          },
          {
            html: "Only require unique Template ID's in New and UpdateTemplate objects"
          },
          {
            html: "Add TVDb to the list of Connections to search in the internal Task to set the Series IDs"
          },
          {
            html: "Properly handle blank results from TVDb when searching for a Series or Episode via external ID"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Comic Book",
            children: [
              {
                html: "Limit angle fields between 0 and 360 degrees"
              }
            ]
          },
          {
            html: "Cutout",
            children: [
              {
                html: "Correctly parse the Blur Profile extra"
              }
            ]
          },
          {
            html: "Overline",
            children: [
              {
                html: "Fix the episode text font size extra"
              }
            ]
          },
          {
            html: "Roman Numeral",
            children: [
              {
                html: "Parse the roman numeral from the episode text directly so it can be modified with the Episode Text Format"
              },
              {
                html: "Correctly display multi-line season text"
              },
              {
                html: "Properly calculate overlapping text for titles with non-default interline spacing"
              }
            ]
          },
          {
            html: "Striped",
            children: [
              {
                html: "Reduce default interline spacing by 20px"
              },
              {
                html: "Improve handling of text boundary calculation for very tall text - no longer raise an uncaught exception if the text is taller than the midpoint of the image"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Improve installation instructions for Unraid users by adding details on how to create template within the UI"
          },
          {
            html: "Add TVDb section to the Getting Started page navigation"
          },
          {
            html: "Add a note about how to add <b>ghcr.io</b> credentials to various Docker managers"
          },
          {
            html: "Fix command on updating container using Docker compose"
          },
          {
            html: "Update \"Add Series\" documentation to reflect new layout and removal of the \"Quick-Add\" concept"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Create <b>POST</b> <b>/api/scheduler/type/{mode}</b> endpoint to explicitly set the Scheduler mode"
          },
          {
            html: "Fix <b>GET</b> <b>/api/settings/version</b> endpoint"
          },
          {
            html: "Create <b>POST</b> <b>/api/reset</b> and <b>POST</b> <b>/api/auth/reset</b> endpoints to reset all of TCM (or all authentication) - these endpoints are disabled for normal usage, and only enabled when TCM is launched in test mode"
          },
          {
            html: "Remove explicit <b>200</b> and <b>201</b> status codes from various <b>/api/fonts</b> endpoints"
          },
          {
            html: "Add <b>imagemagick_executable</b> field to the <b>UpdatePreferences</b> and <b>Preferences</b> API schema"
          },
          {
            html: "Remove <b>delete_missing</b> field from the <b>UpdateFont</b>, <b>NamedFont</b>, and <b>BlueprintFont</b> API schema"
          },
          {
            html: "Add <b>default</b> field to the <b>Extra</b> API schema"
          },
          {
            html: "Modify all <b>GET</b> <b>/api/connection/*</b> endpoints to no longer return plaintext URLs or API keys"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.10.1",
    date: "June 24, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Revise the add Series interaction to no longer launch a separate modal; also removing the \"quick add\" concept"
          },
          {
            html: "Add import from MediUX (i.e. Kometa) button to the Series page"
          },
          {
            html: "Allow connecting to TVDb",
            children: [
              {
                html: "Can be used as an Episode Data Source. This will be similar to Sonarr, but different episode orderings can be used (such as Official, Absolute, etc.)"
              },
              {
                html: "Can also be used as an Image Source, but this is not recommended as they only provide a single (generally low quality) image per-Episode"
              },
              {
                html: "Add SQL schema migration <b>2c1f9a3de797</b> to implement required database changes"
              }
            ]
          },
          {
            html: "Add ability to filter Blueprints by the creator name on the Add page",
            children: [
              {
                html: "Clicking a given Blueprint's creator will auto-fill and search by that creator"
              },
              {
                html: "You can also type <b>by:{creator}</b> or <b>creator:{creator}</b> in the search field - e.g. <b>by:CollinHeist</b>"
              }
            ]
          },
          {
            html: "Also search by the Series \"clean\" name via the search box - e.g. 'Shōgun' can be found by typing 'Shogun'"
          },
          {
            html: "Publish <b>ghcr.io</b> Docker images for the <b>linux/arm64</b> and <b>linux/arm/v7</b> architectures - huge thanks to mchangrh for putting in the work to make the ARMv7 image possible"
          },
          {
            html: "Reformat changelog - remove \"popup\" and create new dedicated changelog page which can accessed from the bottom of the settings page"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Skip Plex episodes which do not have a season or episode number when setting Episode ID's"
          },
          {
            html: "Fix updating the Jellyfin Series ID via the UI"
          },
          {
            html: "Fix poster selection from TMDb - was selecting the <i>lowest</i> priority poster"
          },
          {
            html: "Revise CleanPath subclass implementation to work on some newer versions of Windows 11"
          },
          {
            html: "Fix non-dragging of Cards into Card upload dialog"
          },
          {
            html: "Fix disabling TMDb Connections from the UI and API"
          },
          {
            html: "Correctly handle PNG posters uploaded via the UI and API"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Use improved unicode character replacement suggestions for Font analysis"
          },
          {
            html: "Removed persistent record of \"warned\" series from Plex"
          },
          {
            html: "Use improved database ID matching to Plex episodes when loading Cards"
          },
          {
            html: "Quote the custom ImageMagick executable path in command execution"
          },
          {
            html: "Add trace logging when placeholder titles are ignored from Sonarr"
          },
          {
            html: "Log all relevant environment variables during program boot"
          },
          {
            html: "Add logging of episodes which are <i>not</i> loaded when loading Cards into Plex"
          },
          {
            html: "Update versions of most dependencies (all minor, no re-install required)"
          },
          {
            html: "Change web request caching logic to not cache by request quantity but by request time"
          },
          {
            html: "Slightly reorganize the root directory global settings (cosmetic change only)"
          },
          {
            html: "v1 Rename the <b>plex_libraries</b> setting to <b>libraries</b> (old name is still supported)"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Handle sub directories in the source folder during Source Image deletion"
          },
          {
            html: "Fix some typos in extra tooltips"
          },
          {
            html: "Remove tasks from the scheduler before they are re-initialized"
          },
          {
            html: "Fix text overflow which could occur for some very long series names on the home page in tabular view"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Add \"Episode Text Font Size\" extra - note this behaves a bit weird for much smaller or larger values"
              },
              {
                html: "Add built in character replacements for ＊ and ♥"
              }
            ]
          },
          {
            html: "Formula 1",
            children: [
              {
                html: "v1 Also use under <b>f1</b> card type identifier"
              }
            ]
          },
          {
            html: "Graph",
            children: [
              {
                html: "Correctly handle hidden episode text"
              },
              {
                html: "Actually implement the \"Omit Gradient\" extra"
              }
            ]
          },
          {
            html: "Music",
            children: [
              {
                html: "Limit the music player width to 3000px (was 3200)"
              },
              {
                html: "Do not blur beneath the player when the full image is blurred - minor speed improvement"
              }
            ]
          },
          {
            html: "Notification",
            children: [
              {
                html: "Do not blur beneath the notification(s) when the full image is blurred - minor speed improvement"
              }
            ]
          },
          {
            html: "Poster",
            children: [
              {
                html: "Correctly apply the \"hide episode text\" logic"
              }
            ]
          },
          {
            html: "Shape",
            children: [
              {
                html: "Change the shape scalar multiplier to 130% for multi-line titles (was 125%)"
              },
              {
                html: "Handle math domain errors when the circle size is too small (could happen on very small shapes or very long text)"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Fix handling of non-path custom episode text fonts"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Revise references to PMM as Kometa in the Getting Started Plex page"
          },
          {
            html: "Revise Getting Started to not create two Templates and only create one"
          },
          {
            html: "Create custom 404 page"
          },
          {
            html: "Add page for the <a href=\"https://titlecardmaker.com/card_types/shape/\" target=\"_blank\" rel=\"noopener noreferrer\">Shape</a> card"
          },
          {
            html: "Begin moving old version 1 documentation over to new site"
          },
          {
            html: "Update some Getting Started pages to reflect new page layouts"
          },
          {
            html: "Rewrite Getting Started guide to <i>prefer</i> pulling the <b>ghcr.io</b> Docker packages, instead of the self-build"
          },
          {
            html: "Add TVDb to Connections part of Getting Started tutorial"
          },
          {
            html: "Rewrite series user guide page for new layout"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Create new <b>POST</b> <b>/api/import/series/{series_id}/cards/mediux</b> API endpoint to import Kometa / MediUX YAML cards"
          },
          {
            html: "Create new API endpoints associated with TVDb Connection types",
            children: [
              {
                html: "<b>POST</b> <b>/api/connection/tvdb/new</b> - create a new TVDb Connection"
              },
              {
                html: "<b>GET</b> <b>/api/connection/tvdb/all</b> - get all TVDB Connection details"
              },
              {
                html: "<b>GET</b> <b>/api/connection/tvdb/{id}</b> - get the Connection details of a specific interface ID"
              },
              {
                html: "<b>PATCH</b> <b>/api/connection/tvdb/{id}</b> - update the connection details for TVDb"
              }
            ]
          },
          {
            html: "Change <b>PlexConnection.integrate_with_pmm</b> model field to <b>integrate_with_kometa</b>"
          },
          {
            html: "Change <b>PlexConnection.logo_language_priority</b> model field to <b>logo_language_priority</b>"
          },
          {
            html: "Deprecate <b>POST</b> <b>/api/sources/series/{id}/backdrop</b> endpoint"
          },
          {
            html: "Create new <b>POST</b> <b>/api/sources/series/{id}/backdrop/tmdb</b> and <b>/api/sources/series/{id}/backdrop/tvdb</b> endpoints"
          },
          {
            html: "Add <b>creator</b> query argument to the <b>GET</b> <b>/api/blueprints/query/all</b> endpoint to filter by Blueprint creator"
          },
          {
            html: "Modify <b>GET</b> <b>/api/series/search</b> endpoint to perform a match on the Series clean name (if <b>name</b> argument is provided)"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.10.0",
    date: "May 11, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Completely redesign the Series page",
            children: [
              {
                html: "New page dedicates much less visual space to the poster and action buttons"
              },
              {
                html: "All the prior functionality is still present (if a bit shifted around)",
                children: [
                  {
                    image: "https://titlecardmaker.com/assets/series_light.webp",
                    width: "50%"
                  }
                ]
              },
              {
                html: "Includes a live Card preview which can be used to display present Series <i>and</i> Episode-level changes without saving and remaking a Card"
              }
            ]
          },
          {
            html: "Perform hash validation on all remote card type Python files before they are loaded into the module space"
          },
          {
            html: "Add functionality to directly import Title Cards as \"textless\" when uploaded via the Files dialog"
          },
          {
            html: "Performance improvements on the Templates page",
            children: [
              {
                html: "Hard-code available style list so they do not need to query the availability endpoint"
              },
              {
                html: "Move some asynchronous function calls to <i>after</i> the boilerplate Templates have been added to the page"
              },
              {
                html: "Only query the available Font metadata, not a full query of all Font information"
              }
            ]
          },
          {
            html: "Allow filtering Blueprints by Series name"
          },
          {
            html: "Allow specification of a custom ImageMagick <b>.exe</b> executable path (to use <i>instead of</i> the builtin <b>magick</b> or <b>convert</b> call) by defining the <b>TCM_IM_PATH</b> environment variable"
          },
          {
            html: "Create Striped card type",
            children: [
              {
                html: "I spent <i>way</i> too long creating a very customizable way to adjust the stripe pattern - see <a href=\"https://titlecardmaker.com/card_types/striped/\" target=\"_blank\" rel=\"noopener noreferrer\">the docs</a> for details",
                children: [
                  {
                    image: "https://titlecardmaker.com/card_types/assets/striped.webp",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Rework <b>up triangle</b> and <b>down triangle</b> shapes in the Shape card",
            children: [
              {
                html: "Old triangles were the same width and height (i.e. an isosceles triangle) - new triangles are equilateral"
              },
              {
                html: "Old title text was positioned at halfway up the triangle <i>by height</i> - new text is halfway up <i>by area</i> (e.g. one third by height)"
              },
              {
                html: "For example, old vs. new:",
                children: [
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/88ae682b-6556-420a-b726-02d6e17bf742",
                    width: "25%"
                  },
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/3357565c-dcfd-4be7-aa42-7fbfa96190d7",
                    width: "25%"
                  }
                ]
              },
              {
                html: "This was not done originally because the math to determine the placement of the title and season text is significantly more complicated"
              },
              {
                html: "The old style of triangle generation <b>cannot</b> be used anymore (sorry!)"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Refresh remote card types after a Blueprint is imported"
          },
          {
            html: "Fix downloading Source Images from Emby via the UI"
          },
          {
            html: "Match existing Fonts and Templates by <i>content</i>, not name, when imported via Blueprints"
          },
          {
            html: "Fix Cards ending up hidden when the refresh button was clicked"
          },
          {
            html: "Do not display a cached logo on the Series page"
          },
          {
            html: "Fix creation of new Sonarr connections when no existing Emby, Jellyfin, or Plex connections exist"
          },
          {
            html: "Correctly utilize per-connection localized image rejection (was being ignored)"
          },
          {
            html: "Use versioned CSS files on the frontend - this should prevent some CSS caching issues caused by switching versions"
          },
          {
            html: "Properly handle library names with special URL query characters like <b>&</b> in library operations done via the UI"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Refresh Card previews when the image is clicked on the Font and Template pages"
          },
          {
            html: "Change sidebar text of the add Series page to <b>Add</b> (from <b>Add New</b>)"
          },
          {
            html: "Scroll to the top of the Card preview display when navigating between pages"
          },
          {
            html: "Add click interaction to query available Blueprints when the name is clicked"
          },
          {
            html: "Convert the preview Title Card to <b>.jpg</b> from <b>.webp</b> during Blueprint export (if <b>.webp</b> is the selected card extension)"
          },
          {
            html: "Add the <b>BACKSLASH</b> builtin variable to use <b>\\</b> in format strings"
          },
          {
            html: "Add a button to the home page to swap between the table and poster view"
          },
          {
            html: "Remove the x-axis grid lines from the graphs on the Graphs page"
          },
          {
            html: "Add input to the graphs page to modify how many days are displayed"
          },
          {
            html: "Change all in-UI references from PMM to Kometa"
          },
          {
            html: "Return non-English posters from TMDb if they are textless or the language is present in the connection's language priority setting"
          },
          {
            html: "Add count on the number of Blueprints which are available for a given Series to the Add page"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Do not export <b>Series.auto_split_title</b> in Blueprints if default (True)"
          },
          {
            html: "Fix logo and backdrop visual error when first downloading them via the modal"
          },
          {
            html: "Fix table headers overlapping the search results on the Series page"
          },
          {
            html: "Remove the blacklist button from Blueprints displayed as part of a Set"
          },
          {
            html: "Fix some changelog typos"
          },
          {
            html: "Fix some minor display issues when viewing some Blueprint Sets"
          },
          {
            html: "Handle bad types of external IDs (namely IMDb) from Emby and Jellyfin"
          },
          {
            html: "Properly display an in-UI toast for when no posters are found for a Series"
          },
          {
            html: "Improve handling of corrupt posters found when adding a Series"
          },
          {
            html: "Do not hide the Blueprint pagination menu if only one page of results is displayed (could result in the page menu permanently disappearing until reloading)"
          },
          {
            html: "Add vertical margin between home page posters and pagination menu"
          },
          {
            html: "Handle uncaught exceptions raised during Card creation in the scheduled task - should prevent singular bad cards from stopping all Card creation"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Add kanji font size and stroke width extras"
              }
            ]
          },
          {
            html: "Banner",
            children: [
              {
                html: "Adjust the index text placement down 4 pixels"
              },
              {
                html: "Do not adjust the index text placement with the title vertical shift"
              }
            ]
          },
          {
            html: "Comic Book",
            children: [
              {
                html: "Add support for mask images"
              }
            ]
          },
          {
            html: "Formula 1",
            children: [
              {
                html: "Fix frame year extra"
              },
              {
                html: "v1 Fix custom font evaluation to no longer look at irrelevant font attributes"
              }
            ]
          },
          {
            html: "Notification",
            children: [
              {
                html: "Add the box adjustments extra"
              },
              {
                html: "Make the index text interline spacing, interword spacing, and kerning static (not tied to title characteristics)"
              }
            ]
          },
          {
            html: "Overline",
            children: [
              {
                html: "Fix line width calculation when a custom kerning is specified"
              },
              {
                html: "Add episode text font size extra"
              },
              {
                html: "Fix index text placement when title text is completely hidden"
              }
            ]
          },
          {
            html: "Shape",
            children: [
              {
                html: "Correctly apply custom interword spacing"
              },
              {
                html: "Correctly parse non-integer Shape stroke widths"
              },
              {
                html: "Draw shape <i>below</i> title and season text (not above)"
              },
              {
                html: "Correctly evaluate multi-line title height in the text dimension analysis"
              },
              {
                html: "Completely rework triangle shapes (see Major Changes)"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Parse <b>{title_font}</b> within the episode text font file extra to indicate TCM should use the same font file as the title text (saves specifying the full path)"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Add updated scrolling marquee for all available card types to the documentation home page"
          },
          {
            html: "Replace image for the Series page to reflect new view"
          },
          {
            html: "Add page on <a href=\"https://titlecardmaker.com/user_guide/mask_images/\" target=\"_blank\" rel=\"noopener noreferrer\">mask images</a>"
          },
          {
            html: "Fix keyboard shortcut icons on the Blueprint Set page"
          },
          {
            html: "Begin page on the <a href=\"https://titlecardmaker.com/card_types/anime\" target=\"_blank\" rel=\"noopener noreferrer\">Anime</a> card"
          },
          {
            html: "Add documentation on the Font title split modifier option"
          },
          {
            html: "Add ImageMagick installation instructions to the getting started page"
          },
          {
            html: "Create card type page for the new <a href=\"https://titlecardmaker.com/card_types/striped/\" target=\"_blank\" rel=\"noopener noreferrer\">Striped</a> card"
          },
          {
            html: "Use titlecardmaker.com hosted images for all card previews on the home page"
          },
          {
            html: "Lazy load all card previews on the home page"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Create API endpoint <b>PUT</b> <b>/api/series/series/{series_id}/copy</b> to copy the Series config from one Series to another"
          },
          {
            html: "Make the <b>year</b> argument optional in the <b>GET</b> <b>/api/blueprints/query/series</b> endpoint"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.9.1",
    date: "March 27, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Allow Series level toggle of title auto-splitting",
            children: [
              {
                html: "Add SQL schema and migration <b>f1692007cf8a</b> to add the <b>Series.auto_split_title</b> column"
              },
              {
                html: "Migrate all <b>True</b> Episode-level splits to null"
              }
            ]
          },
          {
            html: "Allow named Fonts to affect after how many characters TCM will attempt to split titles into multiple lines",
            children: [
              {
                html: "All Named Fonts can specify a \"Title Split Modifier\" which is the number of characters to add/remove from the card's default split amount."
              },
              {
                html: "For example, if a Card typically splits lines after 25 characters, specifying a modifier of +5 would mean the titles would be split after <i>30</i> characters."
              },
              {
                html: "This can be used to give more fitting behavior for Fonts which are very small or very large"
              },
              {
                html: "Add SQL schema <b>1be1951acc40</b> to add the <b>Font.line_split_modifier</b> column"
              }
            ]
          },
          {
            html: "Allow card types to adjust the title split behavior on-the-fly",
            children: [
              {
                html: "After how many characters a Title is split is now scaled by the specified font size (if the default Font is specified)"
              }
            ]
          },
          {
            html: "Separate the watched and recently added Tautulli agents",
            children: [
              {
                html: "Allows <i>only</i> enabling the recently added trigger; or enabling both"
              },
              {
                html: "Add a \"username\" input to the Tautulli setup modal so the watched agent can only be triggered when you watch content"
              },
              {
                html: "Old agents will still work"
              }
            ]
          },
          {
            html: "Create a \"Missing\" page (<b>/missing</b>) which lists all the Episodes which do not have an associated Title Card"
          },
          {
            html: "Allow creation of Blueprint \"Sets\"",
            children: [
              {
                html: "A \"Set\" is a group of associated Blueprints. These can be Blueprints which all use the same style, or are part of the same franchise, etc."
              },
              {
                html: "For example, I created a Set of all my Scooby-Doo Blueprints as they all use the same design, Template, and Font"
              },
              {
                html: "If a Blueprint has any associated Sets, it will be displayed on the Blueprint itself",
                children: [
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/324874a2-5508-43f3-9d40-57748125b7dc",
                    width: "50%"
                  }
                ]
              },
              {
                html: "Sets of <i>existing</i> Blueprints can be created directly on the Blueprints GitHub via this <a href=\"https://github.com/TitleCardMaker/Blueprints/issues/new/choose\" target=\"_blank\" rel=\"noopener noreferrer\">issue form</a>."
              },
              {
                html: "New Blueprints can be assigned to existing Sets when they are submitted"
              }
            ]
          },
          {
            html: "Add functionality to upload Cards directly to a Series to import them"
          },
          {
            html: "Display a small count number - e.g. <b>(3)</b> - in the Blueprint tab menu on the Series page. This count represents how many Blueprints are available for the Series (idea from bugmacnx)"
          },
          {
            html: "Begin redesign of the Series page; currently can only be accessed by defining the <b>TCM_NEW_SERIES_VIEW</b> environment variable as <b>TRUE</b>"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Query and delete old Loaded assets by Episode ID (not Card) when loading Title Cards"
          },
          {
            html: "Fix Episode title translation for various regional languages which were using their \"fallback\" languages"
          },
          {
            html: "Correctly parse the global card quality setting"
          },
          {
            html: "Handle TMDb movie IDs in Emby episode parsing"
          },
          {
            html: "Do not link the edit of Episode and Series extra fields"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Do not instantiate <b>Title</b> objects during <b>EpisodeInfo</b> initialization - minor speed improvement"
          },
          {
            html: "Do not add intermediate background task queue for Card creation - minor speed improvement"
          },
          {
            html: "Add airdate column to the Episode data tables (advanced mode only)"
          },
          {
            html: "Only keep log records for one week, not two"
          },
          {
            html: "Do not include the <b>delete_missing</b> attribute in Font exports in Blueprints if <b>True</b>"
          },
          {
            html: "Scroll to the top of the page when navigating between pages of Blueprints"
          },
          {
            html: "Add \"rich\" representation of all SQL models to tracebacks"
          },
          {
            html: "Force delete and re-create the Card when the preview is right-clicked on the Series page"
          },
          {
            html: "Add global option to enable/disable Card interactions like the left- and right-click functionality on the Series page"
          },
          {
            html: "Rename \"Sync Specials\" setting to \"Enable Specials\" to avoid conflation with the \"Sync\" feature"
          },
          {
            html: "Remove the support button from the header"
          },
          {
            html: "Improve logging for changes to an existing Card config"
          },
          {
            html: "Change update info frequency on series page to 90 seconds (from 60)"
          },
          {
            html: "Remove <b>preferences.yml</b> YAML import from the importer page - it is way easier and less error prone to just adjust the settings directly."
          },
          {
            html: "Indicate the loading status during Episode extra changes"
          },
          {
            html: "Add click interaction to the Source Image previews - modal will be launched when the preview image is clicked"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Fix the \"Forgot Password?\" link on the login page - was using old website URL"
          },
          {
            html: "Properly set the modal headers when browsing logos and backdrops"
          },
          {
            html: "Initialize the log level dropdown <i>before</i> querying for Logs so it can be interacted with while the page loads"
          },
          {
            html: "Use a centered Unicode bar character <b>｜</b> in the library dividers for better vertical alignment"
          },
          {
            html: "Do not display Loaded asset counts which exceed the Card count"
          },
          {
            html: "Allow the Series Episode data table to take up the full container width on very large displays"
          },
          {
            html: "Remove blank fields from Blueprint JSON exports"
          },
          {
            html: "Fix tooltip typo in the Music card"
          },
          {
            html: "Fix link typo in changelog"
          },
          {
            html: "Fix the next/previous Episode buttons in the edit Episode extra modal from resetting after submitting changes"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Add Kanji stroke color extra"
              },
              {
                html: "Correctly scale the kanji stroke width with the Font stroke width"
              }
            ]
          },
          {
            html: "Banner",
            children: [
              {
                html: "Change lower title text margin to 40 pixels (from 20)"
              }
            ]
          },
          {
            html: "Music",
            children: [
              {
                html: "Change the default long-line truncation behavior to three lines (from two)"
              },
              {
                html: "Adjust the title split cutoff based on the specified player width"
              },
              {
                html: "Limit player inset between 0 and 1200 pixels"
              }
            ]
          },
          {
            html: "Tinted Glass",
            children: [
              {
                html: "Add rounding radius extra"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Add documentation on Blueprint Sets"
          },
          {
            html: "Revise Tautulli getting started docs to mention new separate agents"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Modify the <b>GET</b> <b>/api/statistics/snapshots</b> endpoint",
            children: [
              {
                html: "Add <b>previous_days</b> query parameter to control how many days of snapshots to return"
              },
              {
                html: "Add <b>slice</b> query parameter to every n-th snapshots to return"
              }
            ]
          },
          {
            html: "Deprecate and remove <b>POST</b> <b>/api/import/series/{series_id}/cards</b> endpoint"
          },
          {
            html: "Create new <b>POST</b> <b>/api/import/series/{series_id}/cards/files</b> endpoint to upload Card files directly"
          },
          {
            html: "Create new <b>POST</b> <b>/api/import/series/{series_id}/cards/directory</b> endpoint to import Cards via directory searching"
          },
          {
            html: "Modify all Blueprint database dependency query arguments (affects all endpoints which have this injection)",
            children: [
              {
                html: "Rename <b>refresh_database</b> query argument to <b>force_refresh</b>"
              },
              {
                html: "Add <b>allow_refresh</b> query argument on whether to <i>allow</i> a refresh from an \"expired\" database"
              }
            ]
          },
          {
            html: "Create <b>POST</b> <b>/api/cards/preview/episode/{episode_id}</b> endpoint to create a preview Card for a given Episode",
            children: [
              {
                html: "Functionally equivalent to the <b>/api/cards/episode/{episode_id}</b> endpoint, but does not write to the database and writes the file to the preview directory"
              }
            ]
          },
          {
            html: "Create <b>GET</b> <b>/api/episodes/series/{series_id}/overview</b> endpoint to get \"overview\" info of a Series' Episodes"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.9.0",
    date: "March 10, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Create new Music card type",
            children: [
              {
                image: "https://titlecardmaker.com/card_types/assets/music.webp",
                width: "50%"
              }
            ]
          },
          {
            html: "Create new Notification card type",
            children: [
              {
                image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/8959d3ad-7ae5-4d5f-80fb-194dfbcd09a2",
                width: "50%"
              }
            ]
          },
          {
            html: "Create new Formula 1 card type",
            children: [
              {
                image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/27b833c8-bd7d-4235-8c54-aa5b1aa30bd5",
                width: "50%"
              }
            ]
          },
          {
            html: "Display Source Images from Emby and Jellyfin within the UI when browsing images per-Episode"
          },
          {
            html: "Add option to specify any number of global default Templates",
            children: [
              {
                html: "These Templates are a priority below all other overrides, but just above global settings"
              },
              {
                html: "This should allow very fine-tuned control of all Series in TCM (especially when used with filters)"
              }
            ]
          },
          {
            html: "Completely redo how extras are displayed in Templates, Series, and Episodes",
            children: [
              {
                html: "All available extras are shown in a tab-separated section"
              },
              {
                html: "Extra descriptions and tooltips are now always visible"
              }
            ]
          },
          {
            html: "Display all log available log files within the UI (on the <b>/logs</b> page)"
          },
          {
            html: "Add color \"bubbles\" to Extras and alongside Font color inputs to give a small display of the indicated color"
          },
          {
            html: "Add buttons to analyze the palettes of logo and backdrop files within the UI"
          },
          {
            html: "Allow specification of global per-card type extras"
          },
          {
            html: "Significantly improve the text height measurement algorithm",
            children: [
              {
                html: "Measure text metric ascent and descent instead of directly reported height (these are unreliable, for some reason)"
              },
              {
                html: "Account for non-0 font interline spacing in height measurement for multi-line text"
              },
              {
                html: "In my tests, this meant that manual height-adjusted components - like the bounding box in the Landscape, Comic Book, Tinted Glass, and Music cards; or the kanji placement in the Anime card - are<i>much</i>more accurate"
              }
            ]
          },
          {
            html: "Add previous and next arrows to Episode translation/extra modals to allow quickly navigating between sequential Episodes"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix the localized image setting for TMDb Connections"
          },
          {
            html: "Add <b>colorama</b> and <b>win32-setctime</b> to Pipfile to fix dependency installs in non-Docker on Windows"
          },
          {
            html: "Do not require a Source Image when creating Cards with the Logo card"
          },
          {
            html: "Fix Emby Series ID assigment"
          },
          {
            html: "Allow clearing Series IDs within the UI"
          },
          {
            html: "Apply more strict Episode database ID matching to prevent a single \"bad\" database ID from resulting in false matches - especially for multi-episodes within Plex which are tied to one episode within TVDb / TMDb / IMDb",
            children: [
              {
                html: "If more than one database ID is present, then any two ID matches are required in the database query"
              }
            ]
          },
          {
            html: "Fix for non-Docker Window Title Card previews"
          },
          {
            html: "Handle Series names with apostrophes"
          },
          {
            html: "Still query non-TMDb Connections for Source Images if the Episode does not exist on TMDb"
          },
          {
            html: "Add missing Episode Font kerning column to Episode data tables"
          },
          {
            html: "Fix the specification of per-Episode size, and stroke width within Episode data tables"
          },
          {
            html: "Fix deletion of associated Loaded assets when removing a Connection"
          },
          {
            html: "Correctly reset the global Episode Data Source when a Connection is deleted"
          },
          {
            html: "(Potentially) fix some instances where a very long running Task (or busy DB) could cause all Tasks to be skipped and not rescheduled; resulting in no subsequent Task runs (until TCM is restarted)"
          },
          {
            html: "Fix Jellyfin Series ID assignment incorrectly setting the Emby ID"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Group all Fonts that start with a number under the same <b>#</b> header"
          },
          {
            html: "Add the internal Font asset file path to the file name label text"
          },
          {
            html: "Change backup filename format - old backups from before this change will need to be manually deleted"
          },
          {
            html: "Reduce main page left padding by 20px"
          },
          {
            html: "Adjust the Font and Template column widths"
          },
          {
            html: "Add a small color live indicator for above the Font color customization input"
          },
          {
            html: "Simplify Form parsing for Series and Templates"
          },
          {
            html: "Skip parsing log files if the file modification time is before the specified <b>after</b> parameter"
          },
          {
            html: "Change API query start/end messages to <b>TRACE</b> level"
          },
          {
            html: "Add any custom season title under the <b>season_title</b> Card variable (can be used in format strings)"
          },
          {
            html: "Improve background task execution:",
            children: [
              {
                html: "Do not stop pending Tasks after exception is raised"
              },
              {
                html: "Improve traceback printing for any raised exceptions"
              }
            ]
          },
          {
            html: "Improve Template previews:",
            children: [
              {
                html: "Reflect custom episode text formats"
              },
              {
                html: "Reflect card-type default season and episode text (was always \"Season 1\" and \"Episode 1\")"
              }
            ]
          },
          {
            html: "Improve exception logging when CardType validation fails"
          },
          {
            html: "Log when a Task is \"bad\" (e.g. scheduled in the past) and is fixed"
          },
          {
            html: "Print ImageMagick command history as string, not bytes"
          },
          {
            html: "Resize posters with Pillow, not ImageMagick, so poster generation does not fail when ImageMagick is not installed"
          },
          {
            html: "Use fuzzy searching when finding mask images in Card creation",
            children: [
              {
                html: "Look for masks like <b>(name)-mask.*</b> or <b>(name)_mask.*</b> to support any image type, and more generalized file naming"
              },
              {
                html: "Search for series-wide mask <b>mask.*</b> file if Episode-specific mask is not found"
              }
            ]
          },
          {
            html: "Removed animation from graph page as it made toggling individual elements slow"
          },
          {
            html: "Add <b>format_date()</b> format function to customize the format of an airdate in episode text (or anything else)"
          },
          {
            html: "Refer to Plex labels as \"labels\" and not \"tags\" within the help text in Plex Sync modals"
          },
          {
            html: "Add Exception traceback to log entries on the log page"
          },
          {
            html: "Remove <b>Download Page</b> button from the logs page"
          },
          {
            html: "Increase the bullet point margin in the changelog"
          },
          {
            html: "Make the changelog full screen"
          },
          {
            html: "v1 Allow multi-line season titles on season posters made with the mini maker"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Fix the Series sort order when searching by name"
          },
          {
            html: "Remove redundant Series name / info in some log messages"
          },
          {
            html: "Fix annotated text for when episode text is hidden in the Standard card"
          },
          {
            html: "v1 Properly detect custom Fonts archives from extras for the Comic Book card"
          },
          {
            html: "Correct the description text for the home page size setting"
          },
          {
            html: "Do not set the internal use_(Connection) variables if all Connections of that type are disabled"
          },
          {
            html: "Correctly resize the Source Image when the border is hidden in the Marvel card"
          },
          {
            html: "_Actually_ expire login tokens after 7 days, not 2"
          },
          {
            html: "Correctly detect local episode text font files in the Tinted Frame card"
          },
          {
            html: "Handle exceptions raised during poster downloads"
          },
          {
            html: "Handle invalid API response from Jellyfin when querying Episode watched statuses"
          },
          {
            html: "Add generic metric data to Card preview generation"
          },
          {
            html: "v1 Fix SVG to PNG logo conversion"
          },
          {
            html: "Handle AttributeError caused by bad TMDb API returns in the TMDb find Episode logic"
          },
          {
            html: "Properly evaluate missing Source Images for card types which do not use unique Source Images (namely the Poster card)"
          },
          {
            html: "Resize poster thumbnails uploaded directly via API to 750 pixels, not 500"
          },
          {
            html: "Resize mask images (to 3200x1800) before applying to Title Card"
          },
          {
            html: "Fix Card importing when a directory is not specified"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Color kanji stroke using the <i>kanji color</i>, not title color"
              }
            ]
          },
          {
            html: "Banner",
            children: [
              {
                html: "Increase right margin between text on bottom line of title text to 55 pixels (from 30)"
              }
            ]
          },
          {
            html: "Comic Book",
            children: [
              {
                html: "Fix index text box placement (was being offset by index text width, not height)"
              }
            ]
          },
          {
            html: "Graph",
            children: [
              {
                html: "Limit graph inset between 0 - 1800 pixels"
              },
              {
                html: "Limit graph radius between 50 and 900 pixels"
              },
              {
                html: "Force the graph width to always be less than or equal to the graph radius"
              }
            ]
          },
          {
            html: "Landscape",
            children: [
              {
                html: "Add box width extra"
              }
            ]
          },
          {
            html: "Logo",
            children: [
              {
                html: "Add logo size and logo vertical shift extras"
              },
              {
                html: "Do not create intermediate resized logo image, instead using an inline image queue (will speed up Card creation a lot)"
              },
              {
                html: "Add episode text color extra"
              },
              {
                html: "Add episode text vertical shift extra"
              }
            ]
          },
          {
            html: "Olivier",
            children: [
              {
                html: "Add omit gradient extra"
              }
            ]
          },
          {
            html: "Roman Numeral",
            children: [
              {
                html: "Fix season text height calculation for multi-line season text"
              }
            ]
          },
          {
            html: "Shape",
            children: [
              {
                html: "Limit the shape inset extra to between 0 - 1800 pixels"
              },
              {
                html: "Add extra for shape stroke color and width"
              }
            ]
          },
          {
            html: "Standard",
            children: [
              {
                html: "Add episode text vertical shift extra"
              }
            ]
          },
          {
            html: "Textless",
            children: [
              {
                html: "Make source images optional to make the card work easier with Card imports"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Change the default frame width to 5 pixels (from 3)"
              }
            ]
          },
          {
            html: "Tinted Glass",
            children: [
              {
                html: "Move all text down 50 pixels by default"
              },
              {
                html: "Add vertical adjustment extra to control vertical positioning of text"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Add documentation to home page on how to update and switch branches"
          },
          {
            html: "Add card preview URLs for missing card types to the home page carousel"
          },
          {
            html: "Create new pages for the new <a href=\"https://titlecardmaker.com/card_types/notification/\" target=\"_blank\" rel=\"noopener noreferrer\">Notification</a> and <a href=\"https://titlecardmaker.com/card_types/music/\" target=\"_blank\" rel=\"noopener noreferrer\">Music</a> cards which list and give visual examples of supported customizations"
          },
          {
            html: "Remove unrendered nav items in site building"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Add new <b>TRACE</b> LogLevel"
          },
          {
            html: "Add <b>exception</b> field to <b>LogEntry</b> model"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.8.1",
    date: "January 29, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add previous and next buttons to the Source Image modal to easily switch between Episodes when manually selecting Source Images"
          },
          {
            html: "Display Series-relevant logs on the Series page"
          },
          {
            html: "Add new <b>Reference File</b> Template filter argument",
            children: [
              {
                html: "This can be used to filter the Template by the existence of an arbitrary file"
              }
            ]
          },
          {
            html: "Add new global \"Card quality\" setting",
            children: [
              {
                html: "This setting adjusts the JPEG / PNG compression quality used in Card creation"
              },
              {
                html: "The default value is 95 (slightly higher than the default ImageMagick card quality)"
              },
              {
                html: "Only applies to <b>.jpg</b>, <b>.jpeg</b>, and <b>.png</b> card extensions"
              }
            ]
          },
          {
            html: "Rewrite how cardinal and ordinal numbers are specified",
            children: [
              {
                html: "Old-style <b>_cardinal</b> and <b>_ordinal</b> variable postfixes are removed"
              },
              {
                html: "New style is to call the <b>to_cardinal()</b> and <b>to_ordinal()</b> functions in the format string"
              },
              {
                html: "Add SQL data migration to automatically convert any existing season titles and episode text formats to this new syntax"
              },
              {
                html: "<b>All non-English cardinal/ordinal numbers will need to be changed manually</b> - e.g. <b>{season_number_cardinal_fr}</b> should now be <b>{to_cardinal(season_number, 'fr')}</b>"
              },
              {
                html: "Remove global \"translation language\" option"
              },
              {
                html: "This change will speed up and allow for greater flexibility in Card creation"
              }
            ]
          },
          {
            html: "Rewrite all internal logging",
            children: [
              {
                html: "No longer use builtin <b>logging</b> module, use <b>loguru</b>"
              },
              {
                html: "Enable better traceback printouts (tracebacks now display variable values)"
              },
              {
                html: "Log data in <b>.jsonl</b> (JSON-line) format to better handle multi-line log messages"
              },
              {
                html: "Do not write API context IDs to the stdout/stderr output"
              }
            ]
          },
          {
            html: "Allow for Sonarr Sync filtering by Series root folder"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix Series deletion in in Sync delete API endpoint"
          },
          {
            html: "Handle Cards without Episodes in <b>32ef3d4633ce</b> SQL schema migration"
          },
          {
            html: "Correctly load Title Cards for Series with more than one library when not in library-unique-Card mode"
          },
          {
            html: "Correctly apply Series translations when the Series has no libraries"
          },
          {
            html: "Do not allow multiple Syncs to run at once (which could cause a Series to be added multiple times)"
          },
          {
            html: "Do not auto-sort Font replacements",
            children: [
              {
                html: "Add SQL schema <b>3122c0553b1e</b> to separate the <b>Font.replacements</b> JSON column into the two paired <b>Font.replacements_in</b> and <b>Font.replacements_out</b> list columns"
              }
            ]
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Allow advanced format string specifications in:",
            children: [
              {
                html: "Season sub folder naming (this will allow users to omit season sub folders completely by specifying format as <b>{''}</b>)"
              },
              {
                html: "Season title ranges"
              }
            ]
          },
          {
            html: "Add more verbose logging for when a Translation \"fails\""
          },
          {
            html: "Reject \"fake\" translations which exactly match their original titles"
          },
          {
            html: "Update <b>tmdbapis</b> and <b>pillow</b> dependency version(s)"
          },
          {
            html: "Change the default error toast display time to 7.5 seconds (from 5.0s)"
          },
          {
            html: "Add new <b>titlecase()</b> function to format strings"
          },
          {
            html: "Add new <b>to_short_ordinal()</b> function for format strings"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Commit Series changes to the database <i>before</i> refreshing card types"
          },
          {
            html: "Handle Plex API errors raised during watched status querying"
          },
          {
            html: "Delete unlinked Episodes in clean database Task"
          },
          {
            html: "Auto-increment Series IDs to avoid any cache-clashes after deleting a Series"
          },
          {
            html: "Handle transparencies of <b>0.0</b> in Inset card"
          },
          {
            html: "Correctly utilize custom Font interline and interword spacing in the Inset card"
          },
          {
            html: "Correctly utilize custom Font interline spacing in the Banner card"
          },
          {
            html: "Correct the display toast text when manually starting a Sync"
          },
          {
            html: "Fix the index text banner shift extra in the Comic card"
          },
          {
            html: "Add <b>.ttc</b> fonts to the whitelist for the Font file upload input"
          },
          {
            html: "Import Blueprint within background task when importing Series <i>and</i> Blueprint to avoid missing Blueprint Episode overrides if Series Episode data is still being refreshed"
          },
          {
            html: "Use <b>\"\"\"\"</b> syntax in format string evaluation to allow for \" and ' characters"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Anime",
            children: [
              {
                html: "Add the kanji color and episode stroke color extras (contributed by Reicha7)"
              },
              {
                html: "Do not apply custom Font stroke widths to the kanji text"
              }
            ]
          },
          {
            html: "Graph",
            children: [
              {
                html: "Reduce the default graph text font size from 75 to 70"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Automatically search for episode text font files (if specified) next to the Source Image; this means these Font files can be imported directly via Blueprints"
              },
              {
                html: "Allow specification of \"random\" frame colors - specify as <b>random[color1, color2]</b> - e.g. <b>random[red, blue]</b> will randomly select red or blue"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Create a <a href=\"https://titlecardmaker.com/getting_started/terminology/\" target=\"_blank\" rel=\"noopener noreferrer\">Terminology</a> page to the Getting Started tutorial to explain some of the basic terms of TCM"
          },
          {
            html: "Create a <a href=\"https://titlecardmaker.com/user_guide/variables/\" target=\"_blank\" rel=\"noopener noreferrer\">Variables</a> page which details all the available variables for use in format strings"
          },
          {
            html: "Modify Getting Started commands to list the single-line docker commands (was causing issues on Windows)"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Allow pipe (<b>|</b>) separated query strings in the log endpoint (<b>GET</b> <b>/api/logs/query</b>)"
          },
          {
            html: "Change log level names to their uppercase equivalent"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.8.0",
    date: "January 17, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add support for multiple of each type of Connection - e.g. two Sonarr servers, two Plex servers, etc.",
            children: [
              {
                html: "Rewrite a majority of the backend to support an arbitrary number of Connections and libraries"
              },
              {
                html: "Automatically convert \"Episode is Watched\" Template Filter arguments"
              },
              {
                html: "Allow for multiple libraries per-server per-Series and library-specific Title Card creation - e.g. you can now have a Plex TV, TV 4K, Emby TV, TV 4K, <i>and</i> Jellyfin TV, TV 4K library for a single Series (but why would you?)"
              },
              {
                html: "Add global option to enable per-library Card naming; this is required to keep separate Cards with separate watched statuses per library"
              },
              {
                html: "Display a Card's library name in the hover text within UI (if setting is enabled)"
              },
              {
                html: "Display error on Settings/Connections sidebar when a Connection is invalid"
              },
              {
                html: "<b>Sonarr libraries will need to be re-assigned</b>"
              }
            ]
          },
          {
            html: "Rewrite Tautulli notification agent integration and endpoint to work with multiple Plex servers",
            children: [
              {
                html: "Tautulli is now a sub-component of a Plex Connection, no longer a separate section on the page"
              },
              {
                html: "<b>Tautulli agents will need to be re-created</b>"
              }
            ]
          },
          {
            html: "Create new Banner, Graph, Inset, and Shape card types",
            children: [
              {
                image: "/public/cards/banner.webp",
                width: "50%"
              },
              {
                image: "/public/cards/graph.webp",
                width: "50%"
              },
              {
                image: "/public/cards/inset.webp",
                width: "50%"
              },
              {
                image: "/public/cards/shape.webp",
                width: "50%"
              }
            ]
          },
          {
            html: "Combine \"Refresh Episode Data,\" \"Download Source Images,\" and \"Add Translation\" tasks / functionality into the \"Create Title Cards\" task / interactions - this replaces the \"Process Series\" buttons/terminology",
            children: [
              {
                html: "This was done because each of these tasks was meaningless without Card creation, and if triggered out-of-sync, then would trigger needless Card re-creations"
              },
              {
                html: "Remove \"Process Series\" button from Series page"
              },
              {
                html: "Change default interval of \"Create Title Cards\" task to every 12 hours"
              }
            ]
          },
          {
            html: "Create tabular view for home page (default view is table; can be toggled in Settings)",
            children: [
              {
                html: "This view allows performing \"batch\" operations to multiple Series at once"
              },
              {
                html: "Shift-clicking/selection functionality is implemented"
              }
            ]
          },
          {
            html: "Create Snapshot SQL table where TCM will periodically take a \"snapshot\" of your DB",
            children: [
              {
                html: "This snapshot notes how many Episodes, Series, Fonts, Title Cards you have; as well as total number of Title Cards created, etc."
              },
              {
                html: "These snapshots can be visualized into a fully interactive graph by clicking <b>View Graphs</b> at the bottom of the home page, like so:",
                children: [
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/f61c7949-b81c-4bda-8501-ca16f3899e46",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Rework home page statistics",
            children: [
              {
                html: "Now they are located at the bottom of the home page"
              },
              {
                html: "Display more types of statistics (e.g. number of Fonts, Templates, etc.)"
              }
            ]
          },
          {
            html: "Automatically redact \"secrets\" from logs (this applies to URLs and API keys)"
          },
          {
            html: "Allow arbitrary Python code inside format strings - not just base <b>str.format</b> data",
            children: [
              {
                html: "Can access any Card variables, as well as <b>NEWLINE</b> for <b>\\n</b>, and <b>to_roman_numeral</b> to convert a number to a roman numeral"
              },
              {
                html: "For example, a title text format of <b>{NEWLINE.join([' '.join(['.'.join(word) for word in line.split(' ')]) for line in title_text.splitlines()])}</b> will automatically insert a period between all non-line splitting letters of each word in the title text - I used this to create Title Cards for Friends like so:",
                children: [
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/2ad83847-857f-4c26-b5f9-3cace17e6a73",
                    width: "50%"
                  }
                ]
              }
            ]
          },
          {
            html: "Allow pre- and post- case-function application (i.e. upper/lower-case) specific Font character replacements",
            children: [
              {
                html: "Any character replacements prefixed with <b>pre:</b> or <b>post:</b> will only apply that replacement once"
              }
            ]
          },
          {
            html: "Add new global settings:",
            children: [
              {
                html: "Option to delete a Series' Source Images when the Series is deleted from the UI"
              },
              {
                html: "Option to delete any \"missing\" Episodes which are in TCM but<i>not</i>in the assigned Episode Data Source"
              },
              {
                html: "Option to reduce in-UI animations (for performance and/or accessibility)"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix Episode source image uploading via UI"
          },
          {
            html: "Fix source image downloading from Emby"
          },
          {
            html: "Utilize SQL cascade orphan deletion to clean up Episode, Card, and Loaded assets when a Series or Episode is deleted"
          },
          {
            html: "Handle invalid cron expressions in Scheduler table initialization"
          },
          {
            html: "Properly utilize a Series' sort name in the repository URL evaluation"
          },
          {
            html: "Properly import Blueprints with multiple pre-existing Templates and Fonts"
          },
          {
            html: "Correct Template ID assignment in the add new Episode endpoint"
          },
          {
            html: "Handle new types of Tautulli API keys (was hexstrings, now can be any string)"
          },
          {
            html: "Correct small-screen size detection (was using monitor size, not window size)"
          },
          {
            html: "Handle bad formatting (mainly newlines) in Scheduler cron expressions"
          },
          {
            html: "Handle explicit line breaks (<b>\\n</b>) in season and episode text"
          },
          {
            html: "Correctly parse some language codes in title translation"
          },
          {
            html: "Automatically retry un-initialized Connections when making requests (previously would require a restart of TCM)"
          },
          {
            html: "Reject bad Source content when manually selecting and uploading an image via the UI"
          },
          {
            html: "Prevent one Task from running multiple times if triggered manually and then a scheduled trigger occurs"
          },
          {
            html: "Escape backslash characters<i>before</i>other command characters to handle titles that start and end with quotes (<b>\"</b>)"
          },
          {
            html: "Add a new scheduled Task to \"clean\" the database and remove duplicate and outdated entries"
          },
          {
            html: "Correctly identify changes to the Card source file (i.e. switching between Art and Unique styles)"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Also display images from Plex when browsing Episode Source Images within UI",
            children: [
              {
                html: "Utilize proxied URL to avoid sending the header X-Plex-Token in the URL (for MITM)"
              },
              {
                html: "Update Source Image download endpoint to reverse-proxy Plex URLs"
              }
            ]
          },
          {
            html: "Do not ignore temporary / placeholder titles from Sonarr or Plex if title matching is enabled - this means Cards will be created with titles like \"TBA\" if triggered via an integration (Tautulli or Sonarr webhook), but will be updated during the next Title Card creation (if new titles are available)"
          },
          {
            html: "Add row-marking to Episode data tables if that Episode is missing a Card"
          },
          {
            html: "Trigger Card (re)creation by clicking on it in the Files tab of the UI"
          },
          {
            html: "Add 'Episode Extras' Template Filter variable (supported operations are listed <a href=\"https://titlecardmaker.com/user_guide/templates/#filters)\" target=\"_blank\" rel=\"noopener noreferrer\">in the docs</a>"
          },
          {
            html: "Utilize SQLAlchemy 2.0 ORM mappings in all tables for better TA and intellisence"
          },
          {
            html: "Utilize randomly selected Title Card as preview in Blueprint export to add variety when exporting multiple Blueprints for a Series (was always the first Card)"
          },
          {
            html: "Compress images with Pillow, not ImageMagick"
          },
          {
            html: "Change input background color for dark mode to <b>#e4e4e4</b> from <b>#ffffff</b> (for those with picky eyes like me)"
          },
          {
            html: "Change search icon for browsing Source Images in UI"
          },
          {
            html: "Automatically restore from backup if SQL migration failed during boot (to avoid future migration changes created by existing intermediate alembic tables)"
          },
          {
            html: "Change <b>Card</b> SQL table primary key to auto-increment (meaning Card IDs will not be reused)"
          },
          {
            html: "Log new Episodes in batches (e.g. <b>Added 20 new Episodes</b> instead of 20x <b>Added new Episode ..</b>)"
          },
          {
            html: "List some builtin variable overrides in extra dropdowns"
          },
          {
            html: "Report filesize statistics in *ibytes not *ibibits"
          },
          {
            html: "Automatically open new Font accordion after creation"
          },
          {
            html: "Allow and handle multi-season season title ranges - e.g. <b>s1e2-s2e3</b>"
          },
          {
            html: "Add ability to force refresh the Blueprint database by right clicking the <b>Browse Blueprints</b> button on the Add Series page"
          },
          {
            html: "Display the Source Image data as a table by default"
          },
          {
            html: "Log Title Card loading as it happens, not after the fact"
          },
          {
            html: "Do not use background tasks for manual Series Episode data refreshing"
          },
          {
            html: "Add input for TCM URL to the Tautulli setup modal (for users whose Web UI is not the same URL as their TCM backend)"
          },
          {
            html: "Log when there are no title translations available from TMDB"
          },
          {
            html: "Create (and make available) various \"metric\" data, like:",
            children: [
              {
                html: "<b>season_episode_count</b> as the number of Episodes in a season; <b>season_episode_max</b> as the maximum episode number in a season; <b>season_absolute_max</b> as the maximum absolute episode number in a season; <b>series_episode_count</b> as the total number of Episodes in a Series; <b>series_episode_max</b> as the maximum episode number in a Series; and <b>series_absolute_max</b> as the maximum absolute episode number in a Series"
              }
            ]
          },
          {
            html: "Use <b>Debug</b> log level by default when loading the logs page"
          },
          {
            html: "Expire all login tokens after 7 days (was 2)"
          },
          {
            html: "Add new <b>Episode Identifier</b> (e.g. <b>S01E03</b>) Template filter to easily allow filtering by specific Episode(s)"
          },
          {
            html: "Change logging context IDs to 6 characters (from 12)"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Display less pagination menus on the files tab to avoid overflow for Series with more than 100 tabs"
          },
          {
            html: "Correctly identify (and do not display) blank change logs"
          },
          {
            html: "Query Episode watched statuses<i>before</i>Source Image selection (in case some Template filter or styling changes the effective source or style)"
          },
          {
            html: "Handle bad Episode data from Jellyfin (caused by bad Series ID)"
          },
          {
            html: "Reduce login animation speed by 300ms"
          },
          {
            html: "Do not require Source Image to exist for Roman Numeral card creation"
          },
          {
            html: "Correctly calculate the bounding box boundaries when using a custom interword spacing with the Landscape card"
          },
          {
            html: "Fix kanji vertical spacing for multi-line titles with custom Fonts in the Anime card"
          },
          {
            html: "Handle more types of generic uncaught exceptions from the TMDb API"
          },
          {
            html: "Refresh Card and File data after Episode deletion"
          },
          {
            html: "Only wait 5 seconds to delete intermediate Blueprint files (down from 15)"
          },
          {
            html: "Fix <b>pyyaml</b> package version 6.0.1 to fix cython bug present in 6.0.0"
          },
          {
            html: "Unescape <b>\\(</b> and <b>\\)</b> in ImageMagick commands on Windows"
          },
          {
            html: "Remove placeholder elements if Series search fails (to avoid appearance of permanent loading)"
          },
          {
            html: "Handle search results without an assigned watch status in Emby and Jellyfin"
          },
          {
            html: "Do not stack Font replacement and season title range input fields on mobile"
          },
          {
            html: "Add minimum 5 second delay between adding Series on the front-end"
          },
          {
            html: "Do not add Source Image HTML elements for images which do not exist"
          },
          {
            html: "Correct the Blueprints repository link on the \"no Blueprints\" popup"
          },
          {
            html: "Add <b>charset-normalizer</b> requirement to Pipfile (fixes some Windows installs)"
          },
          {
            html: "Add pre-pool pinging to DB connection creation, and change connection timeout to 30 seconds - <i>should</i> help with multi-threaded DB reliability"
          },
          {
            html: "Add poster filesize to the Series poster URL to prevent bad browser caches"
          },
          {
            html: "Fix IMDb ID parsing from Emby"
          },
          {
            html: "Do not buffer Python logging (fixes batched logging on some machines)"
          },
          {
            html: "Commit to the Database after each Sync to avoid potential duplication of Series"
          },
          {
            html: "Handle scheduled Tasks whose \"next run\" is in the future during boot"
          },
          {
            html: "Correct the Episode extras modal when an Episode has >1 extra"
          },
          {
            html: "Fix the Template preview generation for when an explicit style is indicated"
          },
          {
            html: "Display extras from local Card types in Extra dropdown fields"
          }
        ]
      },
      {
        title: "Title Card Changes",
        items: [
          {
            html: "Generalize mask overlays, now \"mask\" images can be added to (almost) every single type of Card - for example:",
            children: [
              {
                image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/10beb3ab-378c-45c2-860b-636ba3041a37",
                width: "50%"
              }
            ]
          },
          {
            html: "Calligraphy",
            children: [
              {
                html: "Add a shadow color extra"
              },
              {
                html: "Reduce the maximum logo height to 725px (From 750px)"
              }
            ]
          },
          {
            html: "Cutout",
            children: [
              {
                html: "Allow transparent overlay colors in Cutout card"
              }
            ]
          },
          {
            html: "Divider",
            children: [
              {
                html: "Add a Text Gravity extra"
              }
            ]
          },
          {
            html: "Landscape",
            children: [
              {
                html: "Change the shadow opacity to 85% (was 80%)"
              },
              {
                html: "Add a shadow color extra"
              },
              {
                html: "Enable the bounding box (and use box darkening) by default"
              }
            ]
          },
          {
            html: "Overline",
            children: [
              {
                html: "Change the default line thickness to 9px (from 7)"
              },
              {
                html: "Adjust default interline spacing for title text when the line position is bottom"
              }
            ]
          },
          {
            html: "Standard",
            children: [
              {
                html: "Add episode text font size extra"
              }
            ]
          },
          {
            html: "Star Wars",
            children: [
              {
                html: "Add support for custom Font vertical shifts"
              }
            ]
          },
          {
            html: "Tinted Frame",
            children: [
              {
                html: "Position the logo below the frame, index, and title text in the Tinted Frame card"
              },
              {
                html: "Add a drop shadow to the logo when specified as the middle element"
              },
              {
                html: "Add a shadow color extra"
              },
              {
                html: "Change the shadow opacity to 85% (was 80%)"
              },
              {
                html: "Shift top index text down 3px"
              },
              {
                html: "Utilize even title line splitting"
              },
              {
                html: "Change the title splitting length to 42 characters"
              }
            ]
          },
          {
            html: "White Border",
            children: [
              {
                html: "Add episode text font size extra"
              },
              {
                html: "Add border color extra"
              }
            ]
          }
        ]
      },
      {
        title: "Documentation Changes",
        items: [
          {
            html: "Move setup instructions to the <a href=\"https://titlecardmaker.com/getting_started/\" target=\"_blank\" rel=\"noopener noreferrer\">Getting Started</a> landing page"
          },
          {
            html: "Add scrolling image marquee to the home page with example screenshots from the UI"
          },
          {
            html: "Stylize references to in-UI buttons"
          },
          {
            html: "Create <a href=\"https://titlecardmaker.com/user_guide/templates/\" target=\"_blank\" rel=\"noopener noreferrer\">Templates</a> User Guide page"
          },
          {
            html: "No longer publish docs to RTD - now all docs are on <a href=\"titlecardmaker.com\" target=\"_blank\" rel=\"noopener noreferrer\">titlecardmaker.com</a>"
          },
          {
            html: "Create <a href=\"https://titlecardmaker.com/user_guide/logs/\" target=\"_blank\" rel=\"noopener noreferrer\">Logs</a> User Guide page"
          },
          {
            html: "Replace doc <b>.png</b> assets with <b>.webp</b> for smaller filesize and faster loading"
          },
          {
            html: "Rewrite Connection docs to reflect multi-connection support"
          },
          {
            html: "Create <a href=\"https://titlecardmaker.com/user_guide/scheduler/#advanced-mode\" target=\"_blank\" rel=\"noopener noreferrer\">Scheduler</a> User Guide page"
          },
          {
            html: "Revise Getting Started instructions to explicitly mention the <b>TitleCardMaker-WebUI</b> install directory"
          },
          {
            html: "Add note about Docker \"invalid reference format\" errors and potential fixes"
          }
        ]
      },
      {
        title: "API Changes",
        items: [
          {
            html: "Change default page size for all paginated API endpoints to 100 (from 250)"
          },
          {
            html: "Add API endpoints to perform batch operations like Series deletion, Title Card deletion, un/monitoring, Card loading, etc."
          },
          {
            html: "Standardize API endpoints in the <b>/series</b> router to match other routers"
          },
          {
            html: "Create API endpoint to delete an Episode's Source Image file(s)"
          },
          {
            html: "Always force reload Title Cards in trigger API endpoints"
          },
          {
            html: "Only refresh card types in Episode PATCH endpoint if change occurred"
          },
          {
            html: "Do not perform unmonitored Tasks in the process Series endpoint"
          },
          {
            html: "Add API endpoint to delete a Series within TCM via the Sonarr delete-series API webhook",
            children: [
              {
                html: "The webhook should be configured to <b>POST</b> to <b>{TCM URL}/api/series/sonarr/delete</b>"
              }
            ]
          },
          {
            html: "Do not always re-query Episode watched statuses in Card creation endpoints"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.7.0",
    date: "November 8, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Use new logo",
            children: [
              {
                image: "https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/web-ui/app/assets/logo.png",
                width: "50%"
              }
            ]
          },
          {
            html: "Major documentation revisions",
            children: [
              {
                html: "Relocate all v2 documentation to <a href=\"https://titlecardmaker.com\" target=\"_blank\" rel=\"noopener noreferrer\">titlecardmaker.com</a>"
              },
              {
                html: "Create dynamic auto-generated \"social cards\" for richer link previews in Discord (and other site) - for example:"
              },
              {
                html: ""
              },
              {
                html: "Use site-wide banner for navigation, move table of contents to sidebar (more room for content)"
              },
              {
                html: "Add various pages (including starter Docker and Docker compose pages)"
              }
            ]
          },
          {
            html: "Various Blueprint improvements",
            children: [
              {
                html: "Allow multiple preview files on all Blueprints - hovering over the preview will show a small animation indicating >1 preview file which can be cycled through by clicking"
              },
              {
                html: "Allow arbitrary files to be added to Blueprints. These files are then downloaded into the relevant Source directory when imported"
              },
              {
                html: "Add toggle to the Blueprint browser to only show Blueprints for Series which you have already added to TCM"
              },
              {
                html: "Add toggle to the Blueprint browser to exclude Blueprints which have already been imported (does not work retroactively)"
              },
              {
                html: "Limit the height of Blueprint description fields"
              },
              {
                html: "Add pre-populated database IDs to Blueprint issue forms (when opened via the UI)"
              },
              {
                html: "Relocate repository to TitleCardMaker organization - now at <a href=\"https://github.com/TitleCardMaker/Blueprints\" target=\"_blank\" rel=\"noopener noreferrer\">TitleCardMaker/Blueprints</a>"
              }
            ]
          },
          {
            html: "Use \"fuzzy\" string matching in search toolbar (using Levenshtein Distance between strings)"
          },
          {
            html: "View Title Cards and Source Images within the UI (on the Files tab of a Series' page)"
          },
          {
            html: "Added ability to analyze custom Font files and make character replacement suggestions",
            children: [
              {
                html: "New <b>Analyze Font Replacements</b> button which performs an analysis of the Font for missing characters and makes suggestions for replacements (and warns about irreplaceable characters)"
              },
              {
                html: "Suggestions now look to decompose Unicode characters in their normalized equivalents when searching for replacements - e.g. if <b>é</b> is missing, it will look for <b>É</b>, <b>e</b>, then <b>E</b>, etc."
              },
              {
                html: "Font analysis now looks at empty glyphs in addition to missing glyphs - this should catch instances where the Font was created with blank spaces instead of the glyph being omitted"
              },
              {
                html: "The analysis looks at the titles and translations of all Episodes associated with (even by proxy) the Font"
              }
            ]
          },
          {
            html: "Allow for card-type specific generic season title specification",
            children: [
              {
                html: "Cards can define a <b>SEASON_TEXT_FORMATTER</b> attribute of type <b>Callable[[EpisodeInfo], str]</b> to change the season title text when there is no customization"
              }
            ]
          },
          {
            html: "Various front-end changes",
            children: [
              {
                html: "Make the background color on dark mode slightly darker"
              },
              {
                html: "Move the Connections, Scheduler, and Import tabs under the Settings tab on the side bar"
              },
              {
                html: "Create new Add Series tab under the home page on the side bar (and remove floating button)"
              },
              {
                html: "Add animated loading logo when waiting for Series to load on the home page"
              }
            ]
          },
          {
            html: "Add new <b>absolute_episode_number</b> variable which can be used in variable formats (e.g. episode text formats) and is the absolute number <i>if available</i>, and the episode number if not"
          },
          {
            html: "Add new human readable cron expressions to the Scheduler table (in advanced scheduler mode) - e.g. <b>20 */10 * * *</b> is described as <b>At 20 minutes past the hour, every 10 hours</b>"
          },
          {
            html: "Add healthcheck command, and API endpoint, to Docker container"
          },
          {
            html: "Automatically perform backups of the database and global options before attempting any SQL schema migrations"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Correctly utilize Template ordering",
            children: [
              {
                html: "The SQL template relationships <i>were</i> utilizing implicit ordering by Template ID, but if a non-sequential Template order was applied to a Sync/Series/Episode, then the order would constantly be reset"
              },
              {
                html: "Update SQL schema to <b>25490125daaf</b> which adds an explicit <b>order</b> column to all many-to-many association tables"
              },
              {
                html: "Correctly initialize Sync Template dropdowns with the correct order of Template specifications"
              }
            ]
          },
          {
            html: "Allow force-resetting of passwords by specifying the <b>TCM_DISABLE_AUTH</b> environment variable while booting to avoid potential lockouts"
          },
          {
            html: "Fix name mismatches when importing Blueprints causing duplicate Series entries (matching is now done with database IDs)"
          },
          {
            html: "Use hashed image URLs for source images so they properly reload when modified"
          },
          {
            html: "Fix Episode ID assignment in Jellyfin"
          },
          {
            html: "Correctly load Title Cards into multiple servers when Series has more than one library"
          },
          {
            html: "Correctly apply Plex Sync exclusion tags"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Relocate the y-position of the index text on the Calligraphy card. It is now dynamic with the logo height"
          },
          {
            html: "Paginate the <b>/api/cards/series/{series_id}</b> API endpoint"
          },
          {
            html: "Minor visual changes to the login page",
            children: [
              {
                html: "Add logo above login header"
              },
              {
                html: "Add link to new <a href=\"https://titlecardmaker.com/user_guide/connections/#forgotten-login\" target=\"_blank\" rel=\"noopener noreferrer\">forgotten password</a> instructions"
              }
            ]
          },
          {
            html: "Modified \"help\" tooltips on various pages to not use popups but instead inline help text - this looks better and makes this info always visible (even on mobile)"
          },
          {
            html: "Only keep backups for up to 3 weeks"
          },
          {
            html: "Add connection-thematic-specific coloring to Sync elements"
          },
          {
            html: "Start loading Font preview when directed from Font link"
          },
          {
            html: "Sleep 30 seconds between attempts to load Episode Cards via API endpoints (Tautulli, Sonarr, excplit) - up from 15"
          },
          {
            html: "Add new \"does not contain\" Template Filter condition - can be used for strings and list variables"
          },
          {
            html: "Change Template sidebar icon to not conflict with new logo"
          },
          {
            html: "Add help text to the (un)monitor button below Series posters (was hoverable tooltip)"
          },
          {
            html: "Also open Series search bar by pressing / key"
          },
          {
            html: "Auto-redirect from login page if authentication is disabled"
          },
          {
            html: "Add global \"colorblind\" accessibility option to utilize more distinct colors (primarily in progress bars)"
          },
          {
            html: "Add global option for enabled language codes to allow specification of translated numbers (i.e. Season and Episode text)"
          },
          {
            html: "Refresh (and animate the reloading of) Card statistics when clicked"
          },
          {
            html: "Query Series statistics every 60 seconds (increased from 30)"
          },
          {
            html: "Add header button which links to the current page's relevant documentation if available"
          },
          {
            html: "Modify the sidebar toggle logic - clicking the logo will return to home page if you are not on mobile"
          },
          {
            html: "Add a loading indicator to Blueprint elements while being imported"
          },
          {
            html: "Revise changelog to utilize accordions to make navigation easier"
          },
          {
            html: "Add a note to the Sync page if no Connections are defined"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Handle non-404 errors when downloading Font files from Blueprints"
          },
          {
            html: "Handle permission errors for root folders creation when starting TCM"
          },
          {
            html: "Left-align Blueprint actions on mobile"
          },
          {
            html: "Remove temporary title-match logging when evaluating EpisodeInfo comparisons"
          },
          {
            html: "Add default <b>TZ</b> of <b>UTC</b> to Docker build"
          },
          {
            html: "Add missing placeholder text to some card type dropdowns"
          },
          {
            html: "Change default season text on Calligraphy card to <b>Season {season_number_cardinal}</b> - e.g. <b>Season One</b> (was <b>Season 1</b>)"
          },
          {
            html: "Limit length of file name path components of cards, folders, etc. to 254 characters (could be exceeded if the title was included in the filename)"
          },
          {
            html: "Correctly utilize Card <i>type</i> default Font replacements in Title Card creation"
          },
          {
            html: "Return Series search results by the Series <i>sort</i> name (so case and special character-agnostic)"
          },
          {
            html: "Properly clear new Sync forms after creation"
          },
          {
            html: "Do not show error toasts when statistics cannot be queried on the home page"
          },
          {
            html: "Correctly handle all supported TMDb language codes (was using outdated list)"
          },
          {
            html: "Correct logo downloading from Emby and Jellyfin"
          },
          {
            html: "Wrap pagination menus on the home page on mobile to avoid overflow"
          },
          {
            html: "Do not auto-zoom into text boxes on mobile (particularly iOS) by dynamically adjusting font size to 16px when selected"
          },
          {
            html: "Properly color the \"outside page\" background in some mobile browsers"
          },
          {
            html: "Handle explicitly raised errors (caused by bad Episode data sources) in Refresh Episode Data task"
          },
          {
            html: "Properly handle deleting attributes from the Preferences model without resetting object"
          },
          {
            html: "Correct next/previous navigation between same-named Series"
          },
          {
            html: "Correctly set <i>Options</i> tab as active tab by default to avoid flicker when loading page"
          },
          {
            html: "Only remake Cards for changes to attributes which are actually reflected in the selected Card's card type model",
            children: [
              {
                html: "Remove individual variable columns of the Card SQL table; instead store generic <b>model_json</b> data"
              },
              {
                html: "Update SQL schema to <b>caec4f618689</b> to convert existing Card objects"
              },
              {
                html: "Non-builtin Cards will be remade after migration"
              }
            ]
          },
          {
            html: "Re-query the current page of Series when the sort order is changed on the home page"
          },
          {
            html: "Do not submit separate API requests for adding a Series and importing a Blueprint in one operation"
          },
          {
            html: "Reflect global un/watched style settings in Template previews"
          },
          {
            html: "Attempt to refresh Episode data up to three times in Sonarr webhook API endpoints (for when your EDS is a Media Server and is slow to refresh)"
          },
          {
            html: "Properly detect mobile devices in JS"
          },
          {
            html: "Correctly clear Episode translations in Episode modals"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.6.0",
    date: "October 7, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add API endpoint to trigger Card creation via Sonarr webhook - this is practically identical to the Tautulli trigger (but not for watched-status changes) but works for all Media Servers - setup docs are <a href=\"https://titlecardmaker.readthedocs.io/en/latest/getting_started/connections/sonarr/#webhook-integration\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
          },
          {
            html: "Create new Calligraphy card type",
            children: [
              {
                image: "/public/cards/calligraphy.jpg"
              }
            ]
          },
          {
            html: "Create new Marvel card type",
            children: [
              {
                image: "/public/cards/marvel.jpg"
              }
            ]
          },
          {
            html: "Simplify default directory structure",
            children: [
              {
                html: "Move <b>assets</b>, <b>backups</b>, <b>logs</b>, and <b>source</b> directories under <b>config</b>."
              },
              {
                html: "Move the Database and global options files under <b>config</b>"
              }
            ]
          },
          {
            html: "Explicitly handle and integrate local Python card types into the UI",
            children: [
              {
                html: "Any <b>*.py</b> file will be parsed when launched and on trigger of the <b>RefreshCardTypes</b> task"
              },
              {
                html: "Documentation for integrating cards is available <a href=\"https://titlecardmaker.readthedocs.io/en/latest/card_types/local/\" target=\"_blank\" rel=\"noopener noreferrer\">here</a>"
              }
            ]
          },
          {
            html: "Back up global settings / preferences when performing the <b>BackupDatabase</b> task"
          },
          {
            html: "Toggle side navigation bar completely when the TCM icon is clicked"
          },
          {
            html: "Display changelogs within the UI (<i>you're looking at it!</i>)"
          },
          {
            html: "Write EXIF data to all Plex uploaded images when PMM Integration is enabled"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Correctly display and edit extras in Episode modals"
          },
          {
            html: "Use bottom-heavy titling in Overline card"
          },
          {
            html: "Correct YAML importing to properly sequence imports of Fonts, then Templates, then Series"
          },
          {
            html: "Properly apply custom Fonts to Series when importing YAML"
          },
          {
            html: "Correctly convert season folder format variables when importing YAML"
          },
          {
            html: "Hide home page statistics on mobile to improve formatting"
          },
          {
            html: "Properly initialize, enable, and display the Template special syncing dropdown"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Only query card types once per load on Templates page"
          },
          {
            html: "Filter file browser to accept Font files in upload dialog"
          },
          {
            html: "Filter file browser to accept image files in source, poster, and logo upload dialogues"
          },
          {
            html: "Add note about what Blueprints are to Series page"
          },
          {
            html: "Use global card file type for preview image generation (should be ~50% faster for those with <b>.jpg</b> as their card extension)"
          },
          {
            html: "Modify the Star Wars and Landscape card type descriptions"
          },
          {
            html: "Modify <b>Font.file</b> SQL schema and data to <b>Font.file_name</b>"
          },
          {
            html: "Add <b>--logo</b> mini argument to mini_maker.py to add logo files to created cards"
          },
          {
            html: "Apply Font replacements before and after title text case function and title splitting is applied"
          },
          {
            html: "Add button to quickly add all letters of the alphabet to the preview title in the Font preview"
          },
          {
            html: "Make season title popups uninvertible"
          },
          {
            html: "Add button to add all A-Z/a-z to the example title on Fonts preview"
          },
          {
            html: "Allow specification of \"even\" splitting style in card types (instead of just top / bottom)"
          },
          {
            html: "Add variables for the \"title-case\" version of spelled episode text cardinal and ordinal numbers - i.e. \"One\" instead of \"one\" (only applies to Cards with non-fix cased season/episode text)"
          },
          {
            html: "Add episode text font size extra to Olivier card"
          },
          {
            html: "Add dynamic links to the assigned Fonts for Templates and Series which opens the Font page for easier editing"
          },
          {
            html: "Export Series and Template localized image rejection in Blueprints"
          },
          {
            html: "Add navbar and header via Jinja2 templates, not AJAX injection"
          },
          {
            html: "Add contextual logging to each Alembic SQL schema migration"
          },
          {
            html: "Add logo vertical shift extra to Tinted Frame card"
          },
          {
            html: "Highlight the active page in the nav bar"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Handle bad f-strings in Card <b>logo_file</b> format strings"
          },
          {
            html: "Add more TMDb language codes for translations and logo language prioritization"
          },
          {
            html: "Explicitly attempt the Sonarr and Tautulli integration endpoints multiple (up to 6) times - this should handle instances where the media server is slow to add the new Episode to the server, causing TCM to fail to upload the new Card"
          },
          {
            html: "Only generate number word translations when requested for Card creation"
          },
          {
            html: "Correct preview episode text in card preview endpoint"
          },
          {
            html: "Pass watched attribute into Preview card model so that watched-status specific toggles (not styles) are applied"
          },
          {
            html: "Properly apply blurred grayscale style modifiers to preview cards if watched and unwatched styles are both blurred and grayscale"
          },
          {
            html: "Correctly import the <b>logo_language_priority</b> YAML option"
          },
          {
            html: "v1 Fix Summary image creation"
          },
          {
            html: "Handle bad <b>TZ</b> environment declarations in Docker"
          },
          {
            html: "Export Series <b>match_titles</b> property in Blueprints"
          },
          {
            html: "Use TVDb <b>/dereferrer</b> endpoint in TVDb links"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.5.2",
    date: "September 4, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Match existing Fonts and Templates (by name) when importing Blueprints"
          },
          {
            html: "Add various UI global options:",
            children: [
              {
                html: "How many Series to display per page on the home page"
              },
              {
                html: "How many Episodes to display per page"
              },
              {
                html: "Whether to stylize un-monitored Series posters on the home page"
              },
              {
                html: "Whether to display simplified Episode data tables which only display the most commonly edited columns"
              }
            ]
          },
          {
            html: "Export Font files in a separate sub-zip directory when exporting Blueprints"
          },
          {
            html: "Add warnings to the Series page if the Series is not matched in Emby/Jellyfin/Sonarr/TMDb"
          },
          {
            html: "Add display to start adding a new Series for given query if no results are found in search bar"
          },
          {
            html: "Create Overline card type",
            children: [
              {
                image: "https://user-images.githubusercontent.com/17693271/271863029-e82e411c-8d43-4de8-89f0-470fe007c626.jpg"
              }
            ]
          },
          {
            html: "Automatically search for \"mask\" images to overlay on top of the frame and frame edges in the Tinted Frame card",
            children: [
              {
                html: "TCM will search for files named like <code>{filename}-mask.png</code> - e.g. <code>s1e1-mask.png</code> in the source folder"
              },
              {
                html: "If provided, this mask image is overlayed after the text and frame is drawn"
              },
              {
                html: "This can be used to give the appearance of part of the image extending beyond the boundaries of the frame - for example:"
              },
              {
                image: "https://user-images.githubusercontent.com/17693271/271863036-3e55a94c-b9a6-4e7b-8735-ee8b8fc0c33c.jpg"
              }
            ]
          },
          {
            html: "Merge new user card type <code>azuravian/SciFiTitleCard</code>"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Use version number in Javascript filenames to avoid caching files between versions"
          },
          {
            html: "Correct page load error when loading Series pages with non-default Font kerning and default stroke widths"
          },
          {
            html: "Improve reliability and speed of Tautulli Plex rating key endpoint"
          },
          {
            html: "Delete old Blueprint zips"
          },
          {
            html: "Actually use Font replacements"
          },
          {
            html: "Update <code>Wdvh/WhiteTextStandard</code> to be much faster and integrate better with the UI"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Do not refresh ImageMagick interface(s) after updating global settings"
          },
          {
            html: "Reduce remote card type API endpoint queries on the Series page (improves loading time)"
          },
          {
            html: "Globally query available data on the Series page to significantly improve Episode table loading times"
          },
          {
            html: "Add blank Templates at the top of the Templates list"
          },
          {
            html: "Utilize persistent Jellyfin IDs"
          },
          {
            html: "Add Glass Color extra in Tinted Glass card"
          },
          {
            html: "Use better Series title matching in Plex (for Series without database IDs)"
          },
          {
            html: "Don't display erroneous placeholders for Font values"
          },
          {
            html: "Add additional info to tooltips on the default values of some extras"
          },
          {
            html: "Do not blur edges of source images in the Tinted Frame card when entire image is already blurred (should improve card creation time when blurring is enabled)"
          },
          {
            html: "Remove explicit logo extra from imported Templates YAML"
          },
          {
            html: "Add episode text vertical shift extra to Olivier card"
          },
          {
            html: "Remove warning about Episode missing an absolute number in season title range evaluations"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Handle SQL errors in load all Title Cards task"
          },
          {
            html: "Display more pagination elements by default"
          },
          {
            html: "Properly detect contextual Loggers in decorated functions"
          },
          {
            html: "Do not invert modal un-invertible subcontent"
          },
          {
            html: "Correct CreateTitleCards Task description"
          },
          {
            html: "Correct plural of Episode override count when browsing the Blueprints on the Series page"
          },
          {
            html: "Use contextual logger in remote card type initialization"
          },
          {
            html: "Explicitly sanitize card filenames (should handle explicit \\n in card filenames)"
          },
          {
            html: "Correctly detect hidden episode text in Olivier card"
          },
          {
            html: "Refer to the web-ui branch of the CardTypes repository for all RemoteFile objects"
          },
          {
            html: "Handle more instances of busy databases in scheduled Tasks"
          },
          {
            html: "Handle explicit newlines (<b>\\\\n</b>) in titles for preview card creation"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.5.1",
    date: "August 18, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Rewrite various PlexInterface functions to significantly improve speed of Plex as a Sync and Episode data source"
          },
          {
            html: "Add buttons to the Series page to remove all TCM / PMM labels from within Plex"
          },
          {
            html: "Add scheduled Task to remove \"bad\" Card entries (e.g. duplicates, unlinked, etc.)"
          },
          {
            html: "Use separate colors for \"progress\" bars to differentiate un/monitored Series on the home page"
          },
          {
            html: "Overhaul extra selection to display all supported extras in dropdowns"
          },
          {
            html: "Add various extras to the Tinted Frame card:",
            children: [
              {
                html: "Add <b>episode_text_font</b> to override the Font used for the Episode Text"
              },
              {
                html: "Add <b>episode_text_font_size</b> to adjust the size of the Episode text"
              },
              {
                html: "Add <b>episode_text_vertical_shift</b> to adjust vertical position of Episode text"
              },
              {
                html: "Add <b>frame_width</b> to adjust the width of the frame"
              }
            ]
          },
          {
            html: "Add column to the Episode data table to create a singular Card"
          },
          {
            html: "Add new Font customization option for interword spacing"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix logo as the top/middle element in Tinted Frame card"
          },
          {
            html: "Correctly export Episode extras in Blueprints"
          },
          {
            html: "Keep records of advanced scheduling crontabs between restarts"
          },
          {
            html: "Respect logo size scalar in Tinted Frame boundaries"
          },
          {
            html: "Permit <b>{title}</b> in the global filename format option"
          },
          {
            html: "Fix direction of vertical shifts in the Tinted Glass card (was opposite to the glass box)"
          },
          {
            html: "Fix the Cutout title card on some versions of ImageMagick"
          },
          {
            html: "Handle SVG logos selected via the UI"
          },
          {
            html: "Add button to query TMDb for logos if a Series logo does not already exist"
          },
          {
            html: "Correctly display previously modified extras in the Episode extras modal"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Automatically open and start populating a GitHub issue when the \"Export Blueprint\" button is pressed"
          },
          {
            html: "Allow ordering Blueprints by creation time or Series name"
          },
          {
            html: "Log \"missing\" Series triggers by Tautulli endpoint as info, not errors"
          },
          {
            html: "Remove deleted row from Episode data table without re-querying all Episodes"
          },
          {
            html: "Sequentially transition in Posters on home page, and search results on the new Series page"
          },
          {
            html: "Use dark theme by default"
          },
          {
            html: "Display up to 15 page selectors on the Episode data tab, up to 4 on mobile"
          },
          {
            html: "Only display 50 Episodes/page on Episode data table"
          },
          {
            html: "Use a container size of 500 in PlexInterface functions"
          },
          {
            html: "Add global support for <b>title_text_format</b> extra to apply automatic formatting to title text"
          },
          {
            html: "Show \"internal\" tasks within the UI when Advanced Scheduling is enabled"
          },
          {
            html: "Add new Fonts and Templates to the top of their respective lists"
          },
          {
            html: "Automatically convert filename format arguments from v1 to their v2 equivalents"
          },
          {
            html: "Change default interval for the refresh Episode data Task to 8 hours (from 6)"
          },
          {
            html: "Add headers between Fonts when more than 20 are defined"
          },
          {
            html: "Permit custom Font files in the Roman Numeral card"
          },
          {
            html: "Show up to 15 (5 on mobile) page selectors for Blueprints"
          },
          {
            html: "Add API endpoint to get all Cards, unblacklist Blueprint"
          },
          {
            html: "Display more verbose errors in toasts for 422 validation errors"
          },
          {
            html: "Autofocus on the search field on the new Series page"
          },
          {
            html: "Add <b>blur_profile</b> extra to the Cutout card"
          },
          {
            html: "Add divider_color extra to the Divider card"
          },
          {
            html: "Parse Font interline spacing in the Roman Numeral card"
          },
          {
            html: "Parse Font interline spacing and Kerning in the Cutout card"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Correct interface refreshing triggered by toggling the connection"
          },
          {
            html: "Stop querying or displaying logs, and Series statistics when cookie / session expires"
          },
          {
            html: "Correct contextual logger reference in error decorators"
          },
          {
            html: "Fix Sync modals on mobile (they were too wide)"
          },
          {
            html: "Fix Emby and Jellyfin library dropdown population in Sync modals"
          },
          {
            html: "Do not automatically uppercase season and episode text in Divider card"
          },
          {
            html: "Do not automatically expire DB sessions after commiting"
          },
          {
            html: "Include disabled auto title splitting in Episode Blueprint exports"
          },
          {
            html: "Properly handle missing logos on Fade and Poster title cards"
          },
          {
            html: "Do not display \"negative\" previous Task durations"
          },
          {
            html: "Use the correct slashes in the card directory placeholder text on the Series page"
          },
          {
            html: "Remove Episode ID's from list of batch ID's when manually saved"
          },
          {
            html: "Log the relevant Episode labels when preventing source image selection within Plex"
          },
          {
            html: "Allow empty character replacements in custom Fonts"
          },
          {
            html: "Use inline Form validation on Form page"
          },
          {
            html: "Correctly parse unchecking the \"Delete Missing\" checkbox"
          },
          {
            html: "Fix exporting Episode data in Blueprints when Plex is used as the Episode data source"
          },
          {
            html: "Handle more instances of \"bad\" search results from Sonarr"
          },
          {
            html: "Parse background extra for the Logo card"
          },
          {
            html: "Make Template Filter reference values optional"
          },
          {
            html: "Refresh HTML theme after adding new Template Filter conditions"
          },
          {
            html: "Do not use Background Tasks in the Tautulli / Plex rating key endpoint to avoid race conditions where no cards are loaded if task sequences quickly after card creation"
          },
          {
            html: "Do not \"manually\" refresh Series Episode data after adding a Series from the UI (redundant)"
          },
          {
            html: "Utilize Font stroke width in the Divider card"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.5.0",
    date: "August 4, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Completely revamp the process new Series are added to TCM",
            children: [
              {
                html: "Now the <b>+ New Series</b> button takes you to a separate page where you can interactively search any enabled interface (Emby/Jellyfin/Plex/Sonarr/TMDb) for the Series - a slightly outdated example:",
                children: [
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/63f18412-0ef5-4f4c-9a71-9764802f2b81",
                    width: "50%"
                  }
                ]
              },
              {
                html: "When a Series is selected, you can easily browse any available Blueprints to add the Series and Blueprint immediately"
              },
              {
                html: "Series can also be quickly added to TCM without opening the menu by clicking the Quick-Add button, which uses the last-selected Libraries and Templates"
              }
            ]
          },
          {
            html: "Browse all available Blueprints within the UI",
            children: [
              {
                html: "Below the aforementioned new series adding, any defined Blueprints can be browsed - for example:",
                children: [
                  {
                    image: "https://titlecardmaker.com/assets/blueprint_series_light.jpg",
                    width: "50%"
                  }
                ]
              },
              {
                html: "These Blueprints can then be imported directly, without explicitly searching for the Series - this will import the Series if it does not exist, as well as the Blueprint"
              },
              {
                html: "Any Blueprints you aren't interested in (or have already imported) can be permanently hidden from this part of the UI, but will still appear when searching for that Series explicitly."
              }
            ]
          },
          {
            html: "Allow toggling of an \"Advanced\" Scheduler mode - to allow Tasks to be scheduled via Cron expressions, not just intervals"
          },
          {
            html: "View and browse Series logos within the UI - at the bottom of the Files tab on the Series page the current logo can be viewed; and all available logos on TMDb can be browsed and downloaded"
          },
          {
            html: "Create White Border title card"
          },
          {
            html: "Implement optional authorization to require a valid username/password to access TCM (and the API) - example of the login screen:",
            children: [
              {
                image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/a10f610a-73b3-4905-9c6d-a55ca91a96f4",
                width: "50%"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Correctly read Version file during initialization"
          },
          {
            html: "Correct the automated validation tests run on all Blueprint submissions"
          },
          {
            html: "Fix logos for the Fade title card not being automatically passed into Cards"
          },
          {
            html: "Fix loading of global Preferences when using remote card types forcing a settings reset on each boot"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Only update Preference attributes if changed"
          },
          {
            html: "Separate all CSS/HTML/JS files"
          },
          {
            html: "Order Fonts and Templates by their name"
          },
          {
            html: "Combine un/watched style fields to be more compact"
          },
          {
            html: "Use lazy loading on Blueprint images in Series page"
          },
          {
            html: "Cache remote card types for 6 hours (from 30 minutes)"
          },
          {
            html: "Add tooltip to the theme toggle button"
          },
          {
            html: "Add <b>box_color</b> extra to Landscape card"
          },
          {
            html: "Display total Card progress / percentage beneath the Series poster on the home page"
          },
          {
            html: "Only query Emby/Jellyfin usernames on Connections page load if enabled"
          },
          {
            html: "Add various keyboard navigations:",
            children: [
              {
                html: "Allow tabbing between Series on the home page, and hitting Enter to open page"
              },
              {
                html: "Hitting F or S anywhere to start typing in the Series search box"
              },
              {
                html: "Hit SHIFT and H anywhere to return to the home page"
              }
            ]
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Raise a 404 Exception if a non-existent Font file is deleted via the API"
          },
          {
            html: "Require unique Template specifications in Series, Fonts, Syncs, and Episodes"
          },
          {
            html: "Use contextual logger in Source image replacement endpoint"
          },
          {
            html: "Make some UI formatting improvements for mobile:",
            children: [
              {
                html: "Do not stack the Episode data table"
              },
              {
                html: "Vertically center align header buttons"
              },
              {
                html: "Hide support button"
              },
              {
                html: "Increase sidebar vertical padding"
              },
              {
                html: "Stack file cards"
              },
              {
                html: "Center log table"
              },
              {
                html: "Stack Template columns"
              }
            ]
          },
          {
            html: "Fix race condition triggered by deleting Series and Cards at the same time"
          },
          {
            html: "Only commit changes to global connections<i>after</i>refreshing interface"
          },
          {
            html: "Correct method calls when a Series cannot be found in Emby or Jellyfin"
          },
          {
            html: "Fix contextual logging of uncaught TMDb exceptions"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.4.1",
    date: "July 17, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Rework global Preferences to be a bit less error-prone (purely a behind the scenes change)"
          },
          {
            html: "Only read the most recent log file when querying for new messages within the UI"
          },
          {
            html: "Add option to Sonarr Connection details to only grab Episode data for Episodes that are downloaded (this is a global setting)"
          },
          {
            html: "No longer skip loading remaining Cards into a Series when >3 Card uploads fail"
          },
          {
            html: "Completely overhaul Blueprint submission",
            children: [
              {
                html: "Blueprints are now submitted by just filling out an Issue form on the GitHub, and then automated workflows parse and validate your submission to create and merge the actual Blueprint"
              }
            ]
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Remove default <b>--workers 4</b> server argument from the Dockerfile"
          },
          {
            html: "Require <b>plexapi</b> 4.14.0 to fix PMM integration failing on some servers",
            children: [
              {
                html: "To fix the PMM integration if you are <i>not</i> using Docker, you might need to run <b>pipenv clean</b> then a clean<b>pipenv install</b>"
              }
            ]
          },
          {
            html: "Prevent TCM from grabbing source images of previously loaded Title Cards"
          },
          {
            html: "Require Series match when creating Cards via Tautulli/rating key - it was possible to remake the Card for the wrong Series if the two had the exact same Episode index + title (i.e. <i>Pilot</i> for S01E01)"
          },
          {
            html: "Fix Emby/Jellyfin Syncs"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add improved documentation to pretty much all of the code"
          },
          {
            html: "Use <b>raise .. from ..</b> syntax where applicable"
          },
          {
            html: "Add <b>maxsplit=1</b> arguments to improve string splitting speed where applicable"
          },
          {
            html: "Move <b>require_kanji</b> logic into Anime card model"
          },
          {
            html: "Paginate <b>/api/templates/all</b> endpoint return"
          },
          {
            html: "Use HTML tooltips instead of titles on the Connections page"
          },
          {
            html: "Standardize all MediaServer and EpisodeDataSource subclasses to use the same method argument structure"
          },
          {
            html: "Use contextual logger in decorated functions to log failed GET requests"
          },
          {
            html: "Use <b>sys.exit</b> instead of built-in <b>exit</b> function"
          },
          {
            html: "Add request method to method start log messages (e.g. <b>GET</b>, <b>POST</b>, etc.)"
          },
          {
            html: "Change Emby and Jellyfin to query for Series ID's at runtime (to handle database ID shuffling, which seems to happen?)"
          },
          {
            html: "Change the default global filename format to <b>{series_full_name} - S{season_number:02}E{episode_number:02}</b>"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Add explicit 10-30 second timeouts to all remote content queries to prevent the program from possibly locking"
          },
          {
            html: "Use contextual Logger for:",
            children: [
              {
                html: "Refreshing remote card types when importing Preference YAML"
              },
              {
                html: "Season title range evaluation"
              }
            ]
          },
          {
            html: "Raise 404 if requesting Statistics for a Series, or deleting a Template that DNE via the API"
          },
          {
            html: "Use updated image size methods in AspectRatioFixer and StandardSummary creation via fixer"
          },
          {
            html: "No longer use deprecated <b>ABC.abstractproperty</b> decorator"
          },
          {
            html: "Use correct <b>__slots__</b> iterable in <b>SeasonTitleRanges</b> class"
          },
          {
            html: "Correct <i>Process Series</i> button tooltip to not reference Card loading"
          },
          {
            html: "Explicitly pass connection URLs to <b>__init__</b> methods"
          },
          {
            html: "Correct language in the delete Sync toast"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.4.0",
    date: "January 17, 2024",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add scheduled task to perform automatic database backups - default interval is 1 day, and backups are kept for 4 weeks"
          },
          {
            html: "Allow import and exporting of Blueprints",
            children: [
              {
                html: "A Blueprint is a customization that applies to a specific Series"
              },
              {
                html: "A Blueprint can include any number of Templates, Fonts, Series customizations,<i>and</i>Episode customizations"
              },
              {
                html: "Blueprints are hosted on the new <a href=\"https://github.com/CollinHeist/TitleCardMaker-Blueprints/\" target=\"_blank\" rel=\"noopener noreferrer\">Blueprints</a> repository, which I've started adding some of my own Blueprints to, both as examples and for use"
              },
              {
                html: "Blueprints can be imported into a Series via the new <b>Blueprints</b> tab on the Series page"
              },
              {
                html: "If there are Blueprints available, an example of each will be displayed in the UI, along with the creator, a brief description, and a list of what is included in the Blueprint",
                children: [
                  {
                    image: "https://github.com/CollinHeist/TitleCardMaker/assets/17693271/1a42589e-bf54-48d2-bddf-823cf55097bd",
                    width: "50%"
                  }
                ]
              },
              {
                html: "A Blueprint can be easily exported by clicking the <i>Export Blueprint</i> Button, which will download a .zip file of the Blueprint (as JSON) that you can edit, any associated Font files, and a preview image for the Series."
              }
            ]
          },
          {
            html: "Refresh Episode data for each Series immediately after being Synced"
          },
          {
            html: "Add button (and endpoint) to process entire Series at once, including proper sequencing of Source Image downloading and Card creation"
          },
          {
            html: "Use explicit<i>Refresh Preview</i>button in Named Font card preview instead of auto-change detection"
          },
          {
            html: "Reflect Font title case specification in Named Font card preview"
          },
          {
            html: "Allow Syncs to be edited within the UI"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Correctly commit changes when updating multiple Episodes via endpoint if last Episode object is unchanged"
          },
          {
            html: "Filter out any messages from the \"future\" when displaying them in the UI (typically caused by misaligned timezone)"
          },
          {
            html: "Use the correct Series<i>unwatched</i>style in Episode source file resolution (was using<i>watched</i>style)"
          },
          {
            html: "Allow deletion of any individual season titles (not just the last title) from the UI"
          },
          {
            html: "Fix effective Template determination for _Episodes_"
          },
          {
            html: "Fix homepage sorting by Series name for Series that have numeric names (e.g. <b>1923</b>)"
          },
          {
            html: "Allow specification of manually split Titles by disabling Auto-Split title for that Episode and then putting <b>\\n</b> in the title where you want to force a split"
          },
          {
            html: "Always commit changes to the global Preferences<i>even if</i>the interface is disabled"
          },
          {
            html: "Do not error on bad Series database ID's"
          },
          {
            html: "Properly display the names of uploaded Named Font files within the UI"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Add <b>interword_spacing</b> extra to Frame and Olivier card types"
          },
          {
            html: "Use contextual logger for:",
            children: [
              {
                html: "Failed image download logging"
              },
              {
                html: "Template creation endpoint"
              },
              {
                html: "Interface refreshing"
              },
              {
                html: "Remote Card Type evaluation"
              },
              {
                html: "Changes to the global Preferences"
              },
              {
                html: "ImageMagick prefix determination"
              }
            ]
          },
          {
            html: "Enforce a minimum task interval of 10 minutes (to prevent freezing up the UI if scheduled too frequently)"
          },
          {
            html: "Skip Jellyfin Series ID assignment if all ID's are present"
          },
          {
            html: "Use updated versions of most packages in Pipfile",
            children: [
              {
                html: "Require <b>1.x</b> for Pydantic as I haven't validated v2"
              },
              {
                html: "Move <b>mkdocs</b> to a dev package"
              }
            ]
          },
          {
            html: "Remove \"URL\" form validation from Connections page to allow URL's without a TLD"
          },
          {
            html: "Use hard drive icon instead of sever icon for \"Load Cards into ...\" Buttons to not use the same design for logs and"
          },
          {
            html: "Do not return <b>CardActions</b> object from Card creation or import endpoints"
          },
          {
            html: "Add font replacement for <b>é</b> and <b>É</b> to Comic Book card type"
          },
          {
            html: "Add \"progress bar\" to show percentage of Title Cards created below Series poster"
          },
          {
            html: "Do not show Sync sections for disabled interfaces"
          },
          {
            html: "Change maximum ImageMagick thread count to 12"
          },
          {
            html: "Use <b>magick</b> IM prefix by default"
          },
          {
            html: "Disable various buttons on the Series page after clicking to prevent making duplicate requests"
          },
          {
            html: "Use orange icons on<i>Force Reload ..</i>buttons"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Improve handling of objects with no Template IDs on YAML imports"
          },
          {
            html: "Remove redundant text from error message when there is missing data from an Episode Text Format string"
          },
          {
            html: "Handle SQL <b>OperationalError</b> in TranslateSeries task"
          },
          {
            html: "Disable caching in Sonarr to catch changes in sequential API requests (e.g. Syncing, adding tag, re-Syncing)"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.3.0",
    date: "July 2, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Improve Sonarr Interface initialization times by no longer querying all Series ID's upon init, instead search for the Series via the <b>/lookup</b> API endpoint when querying for a Series"
          },
          {
            html: "Completely overhaul all logging and log messages",
            children: [
              {
                html: "Every API request and top-level function (e.g. scheduled tasks) generate a unique Context ID like <b>aafa3e9eedaf</b> that is logged in all messages corresponding to that function"
              },
              {
                html: "Create <b>/logs</b> API router to query log files"
              },
              {
                html: "Display the status of background tasks in small toasts that in the bottom right corner. These differ from info toasts that directly respond to an action taken (like a button press) which appear in the top right"
              }
            ]
          },
          {
            html: "Allow logs to be viewed within the UI",
            children: [
              {
                html: "Accessible from the green server button / icon on the page header"
              },
              {
                html: "Logs can be filtered within the UI by log level, context ID(s), message substring, start and end time"
              },
              {
                html: "A context ID or start/end time can be clicked on to add as a filter"
              }
            ]
          },
          {
            html: "Use UMASK of <b>002</b> in Dockerfile"
          },
          {
            html: "Handle overriding source files with extras (including format strings) - specify as <b>source_file</b>"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Allow Template booleans to be cleared (False -> True) from within the UI"
          },
          {
            html: "Handle unspecified arguments in connections YAML importing"
          },
          {
            html: "Handle invalid page landings by redirecting to the homepage"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Sort Series on the server rather than client"
          },
          {
            html: "Paginate Episode data table (and corresponding API endpoint) on Series page"
          },
          {
            html: "Only show home page Series navigation menu if there at least two pages"
          },
          {
            html: "Specify four worker processes in Dockerfile (will eventually make this a variable)"
          },
          {
            html: "Remove logging of Preference file changes"
          },
          {
            html: "Remove log message for existing translations"
          },
          {
            html: "Remove log message for failure to meet Template Filter criteria"
          },
          {
            html: "Remove log messages for using cached remote card contents"
          },
          {
            html: "Parse Episode airdates when initializing EpisodeInfo objects from Plex"
          },
          {
            html: "Do not log missing Source images in the scheduled task"
          },
          {
            html: "Use <b>runuser</b> instead of <b>gosu</b> in Dockerfile"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Remove double <b>magick</b> ImageMagick prefix from TintedFrame card"
          },
          {
            html: "Add slight shadow to separate page header from dark themed page content"
          },
          {
            html: "Remove blank toast from Title Card creation response handler"
          },
          {
            html: "Include fake Series name and Episode indices in Card preview generation"
          },
          {
            html: "Log the correct number of identified entries from a Plex Rating Key"
          },
          {
            html: "Remove unequal margin from page header button icons"
          },
          {
            html: "Retry PersistentDatabase transactions up to 5 times to reduce DB corruptions caused by multi-process access"
          },
          {
            html: "Remove some Debug messages erroneously labeled as critical"
          },
          {
            html: "Handle uncaught exceptions during interface dependency refreshing"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.2.2",
    date: "June 21, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Paginate Series homepage for faster loads for very large servers"
          },
          {
            html: "Fix selection of uppercase title case for custom Fonts via UI"
          },
          {
            html: "Fix Card importing force reload for Card importer (checked/unchecked were reversed)"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Pass Episode cardinal/ordinal numbers to all Card types (fixes Olivier / other Card Types)"
          },
          {
            html: "Fix Tautulli integration API endpoints"
          },
          {
            html: "Relocate preferences JSON file to be persistent between Docker instances (now at <b>/config/source/prefs.json</b>)"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Allow Plex rating key API endpoint to work with lists of keys (not just single)"
          },
          {
            html: "Add lazy loading to Series posters on home page"
          },
          {
            html: "Show list of affected Series when deleting a Template via UI"
          },
          {
            html: "Show info toast when starting to source image downloading is initiated via UI"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Increase bottom margin between statistics and series cards on home page"
          },
          {
            html: "Correctly initialize default card extension for Card importer based on global card extension"
          },
          {
            html: "Fix IMDb Series ID for Series with unassigned IMDb ID's (label was showing TVDb)"
          },
          {
            html: "Utilize <b>magick</b> IM 7.0 Command Prefix in Tinted Frame card (this is kind of a test)"
          },
          {
            html: "Add 10 minute misfire grace period to Scheduler - <i>should</i>allow tasks to finish if delayed"
          },
          {
            html: "Fix default <b>box_adjustments</b> in Landscape and Tinted Glass cards"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.2.1",
    date: "June 16, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add internal task to query for and set missing Series ID's every 24 hours by default"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Fix error where logos were being downloaded from TMDb as posters"
          },
          {
            html: "Correct default box adjustments in Landscape and Tinted Glass card Pydantic models"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Remove blank Sync name from Sync delete toast"
          },
          {
            html: "Add green checkmark next to selected Series in Importer dropdown to improve legibiliy"
          },
          {
            html: "Sleep for 30 seconds on SQL OperationalErrors in Sync and Episode Data Refresh tasks"
          },
          {
            html: "Use full width textarea elements on mobile on Importer page"
          },
          {
            html: "Center align the Scheduler table on mobile"
          },
          {
            html: "Make Series page input elements full width"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Correct URI path to blank image in Font preview"
          },
          {
            html: "Minor CSS / layout improvements for the home page on mobile"
          },
          {
            html: "Fix Sonarr library field auto population"
          },
          {
            html: "Fix logo positioning on mobile (was offcenter)"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.2.0",
    date: "June 16, 2023",
    sections: [
      {
        title: "Major Changes",
        items: [
          {
            html: "Add scheduled Task to download any missing Series posters"
          },
          {
            html: "Download Series posters from associated Media Server (e.g. Plex, Emby, Jellyfin) <i>before</i> trying TMDb"
          },
          {
            html: "Add functionality for TCM to \"guess\" and auto-fill the Libraries setting based on your Sonarr root folders"
          },
          {
            html: "Simplify HTML/CSS on all pages so that the header and sidebar are non-sticky elements (reducing weird scrolling oddities)"
          },
          {
            html: "Fix background \"image\" gradient not filling the page on some pages in Chrome"
          },
          {
            html: "Add navigation buttons to Series pages to quickly move between Series (alphabetically)"
          },
          {
            html: "Add Comic Book title card (https://github.com/CollinHeist/TitleCardMaker/issues/343)"
          },
          {
            html: "Vastly improve Emby Syncs:",
            children: [
              {
                html: "Make them much faster by not making individual API requests per-year (weird API bug..)"
              },
              {
                html: "Apply exclusion tags"
              },
              {
                html: "Directly parse Series database ID's while Syncing"
              }
            ]
          },
          {
            html: "Handle changing Jellyfin Series ID's (maybe)"
          }
        ]
      },
      {
        title: "Major Fixes",
        items: [
          {
            html: "Properly merge Episode translations into extras"
          },
          {
            html: "Fix Card preview generation for Templates and Fonts"
          },
          {
            html: "Handle any type of Tautulli API Key (pre API v3.6, API keys were hexstrings, but they are now randomly generated Base64 strings)"
          },
          {
            html: "Allow changing the Font title case from the UI"
          }
        ]
      },
      {
        title: "Minor Changes",
        items: [
          {
            html: "Change images used in Card preview generation"
          },
          {
            html: "Skip and do not warn if a disabled interface is part of the global image source priority in source selection"
          },
          {
            html: "Download Series poster, assign ID's, and refresh Episode data<i>before</i>returning from add new Series API endpoint"
          },
          {
            html: "Update \"get all Series\" API endpoint to optionally order return by name, year, or ID"
          },
          {
            html: "Add additional type annotations"
          }
        ]
      },
      {
        title: "Minor Fixes",
        items: [
          {
            html: "Catch SQL OperationalError exceptions in Episode data refresh scheduled task"
          },
          {
            html: "Handle <b>transparent</b> in Color Title Card fields (this is a bug in the Pydantic modules that I've submitted a PR/fix for, but will only be released in Pydantic v2.0)"
          },
          {
            html: "Fix CSS resulting in a small white rectangle on some browsers for the card type preview on the Settings page"
          },
          {
            html: "Handle Episodes without season/episode numbers in Emby and Jellyfin"
          }
        ]
      }
    ]
  },
  {
    version: "v2.0-alpha.1.0",
    date: "June 14, 2023",
    sections: [
      {
        title: "Initial Release",
        items: []
      }
    ]
  }
];
