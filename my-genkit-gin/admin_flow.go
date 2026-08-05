package main

import (
	"context"
	"fmt"

	"github.com/firebase/genkit/go/ai"
	"github.com/firebase/genkit/go/core"
	"github.com/firebase/genkit/go/genkit"
	"google.golang.org/genai"
)

// AdminTriggerEvent defines the incoming event payload from external tools (e.g., Google Drive, Trello, Canva).
type AdminTriggerEvent struct {
	Source  string                 `json:"source" jsonschema:"description=The event source (e.g. Drive, Trello, Canva)"`
	Event   string                 `json:"event" jsonschema:"description=The event action type (e.g. file_uploaded, card_moved, image_approved)"`
	Payload map[string]interface{} `json:"payload" jsonschema:"description=Key-value metadata and content payload associated with the event"`
}

// DriveDocumentInput defines the input parameters for fetching a document from Google Drive via MCP.
type DriveDocumentInput struct {
	FileID string `json:"fileId" jsonschema:"description=The unique identifier of the file in Google Drive"`
}

// DriveDocumentOutput defines the content extracted from Google Drive.
type DriveDocumentOutput struct {
	FileID   string `json:"fileId" jsonschema:"description=The file ID"`
	Title    string `json:"title" jsonschema:"description=Document title"`
	Content  string `json:"content" jsonschema:"description=Extracted text content of the document"`
	MimeType string `json:"mimeType" jsonschema:"description=MIME type of the document"`
}

// TrelloCardInput defines the input parameters for fetching Trello card details via MCP.
type TrelloCardInput struct {
	CardID string `json:"cardId" jsonschema:"description=The unique ID of the Trello card"`
}

// TrelloCardOutput defines the information retrieved from Trello.
type TrelloCardOutput struct {
	CardID      string   `json:"cardId" jsonschema:"description=The Trello card ID"`
	Title       string   `json:"title" jsonschema:"description=Card title"`
	Description string   `json:"description" jsonschema:"description=Card description"`
	List        string   `json:"list" jsonschema:"description=Current list name (e.g. Done, In Progress)"`
	Labels      []string `json:"labels" jsonschema:"description=Labels attached to the card"`
}

// AstroUpdateInput defines the parameters required to update the Astro website database.
type AstroUpdateInput struct {
	Section string `json:"section" jsonschema:"enum=menu,enum=events,enum=announcements,description=Target section on the Astro website"`
	Title   string `json:"title" jsonschema:"description=Title of the item or update"`
	Content string `json:"content" jsonschema:"description=Main content body or structured JSON data"`
	Status  string `json:"status" jsonschema:"enum=published,enum=draft,description=Publishing status"`
}

// AstroUpdateOutput defines the response after updating the Astro website database.
type AstroUpdateOutput struct {
	Success   bool   `json:"success" jsonschema:"description=True if the database update succeeded"`
	RecordID  string `json:"recordId" jsonschema:"description=Unique ID of the updated/inserted database record"`
	UpdatedAt string `json:"updatedAt" jsonschema:"description=Timestamp of the update"`
}

// GoogleBusinessPostInput defines the parameters required to publish a Google Business Profile update.
type GoogleBusinessPostInput struct {
	Summary  string `json:"summary" jsonschema:"description=Post text summary or announcement"`
	TopicType string `json:"topicType" jsonschema:"enum=STANDARD,enum=EVENT,enum=OFFER,description=Google Business Profile post topic type"`
	CallToAction string `json:"callToAction" jsonschema:"enum=LEARN_MORE,enum=BOOK,enum=ORDER,description=Action button type"`
}

// GoogleBusinessPostOutput defines the result of publishing to Google Business Profile.
type GoogleBusinessPostOutput struct {
	Success bool   `json:"success" jsonschema:"description=True if the post was successfully created"`
	PostURL string `json:"postUrl" jsonschema:"description=Public URL of the published post"`
}

// AdminDecisionResult represents the final structured decision and execution output of the Zero-UI flow.
type AdminDecisionResult struct {
	ActionTaken string `json:"actionTaken" jsonschema:"description=Action executed: WebsiteDBUpdated or GoogleBusinessPostPublished"`
	Target      string `json:"target" jsonschema:"description=Target system modified (AstroDB or GoogleBusinessProfile)"`
	Summary     string `json:"summary" jsonschema:"description=Human-readable summary of the performed action"`
	Success     bool   `json:"success" jsonschema:"description=Overall success status"`
}

// RegisterZeroUIAdminFlow initializes MCP tools and defines the ZeroUIAdminFlow for Genkit.
func RegisterZeroUIAdminFlow(g *genkit.Genkit) *core.Flow[AdminTriggerEvent, *AdminDecisionResult, struct{}] {
	// MCP Tool 1: Fetch Google Drive Document
	fetchDriveDocumentTool := genkit.DefineTool(g, "fetchDriveDocument",
		"MCP Tool: Fetches the text content of a document or PDF file from Google Drive.",
		func(ctx *ai.ToolContext, input DriveDocumentInput) (*DriveDocumentOutput, error) {
			return &DriveDocumentOutput{
				FileID:   input.FileID,
				Title:    "Seasonal Tasting Menu & Wine Pairing 2026.pdf",
				Content:  "Autumn Tasting Menu Update: Introducing Roasted Venison with Juniper Emulsion & Wild Blackberry Reduction. Wine pairing: 2021 Barolo Reserve.",
				MimeType: "application/pdf",
			}, nil
		},
	)

	// MCP Tool 2: Fetch Trello Card
	fetchTrelloCardTool := genkit.DefineTool(g, "fetchTrelloCard",
		"MCP Tool: Fetches card metadata, descriptions, and labels from a Trello board.",
		func(ctx *ai.ToolContext, input TrelloCardInput) (*TrelloCardOutput, error) {
			return &TrelloCardOutput{
				CardID:      input.CardID,
				Title:       "Announce Special Weekend Wine & Dining Event",
				Description: "Publish a post announcing our upcoming Friday Chef's Table experience featuring Barolo Reserve pairings.",
				List:        "Approved for Publication",
				Labels:      []string{"Marketing", "Social Media"},
			}, nil
		},
	)

	// MCP Tool 3: Update Astro Website Database
	updateAstroWebsiteDBTool := genkit.DefineTool(g, "updateAstroWebsiteDB",
		"MCP Tool: Updates the Astro website database with new menu items, events, or restaurant announcements.",
		func(ctx *ai.ToolContext, input AstroUpdateInput) (*AstroUpdateOutput, error) {
			return &AstroUpdateOutput{
				Success:   true,
				RecordID:  fmt.Sprintf("astro_rec_%s", input.Section),
				UpdatedAt: "2026-08-05T16:00:00Z",
			}, nil
		},
	)

	// MCP Tool 4: Publish Google Business Profile Post
	publishGoogleBusinessPostTool := genkit.DefineTool(g, "publishGoogleBusinessPost",
		"MCP Tool: Publishes an official update or event post on the restaurant's Google Business Profile.",
		func(ctx *ai.ToolContext, input GoogleBusinessPostInput) (*GoogleBusinessPostOutput, error) {
			return &GoogleBusinessPostOutput{
				Success: true,
				PostURL: "https://posts.gle/aura-haute-cuisine-autumn-update",
			}, nil
		},
	)

	// ZeroUIAdminFlow Definition
	return genkit.DefineFlow(g, "ZeroUIAdminFlow",
		func(ctx context.Context, input AdminTriggerEvent) (*AdminDecisionResult, error) {
			prompt := fmt.Sprintf(`You are a Zero-UI Autonomous Restaurant Administrator Agent.

An external event has occurred:
- Source System: %s
- Event Type: %s
- Payload Data: %+v

YOUR GOAL:
1. If the event source is "Drive" or "GoogleDrive", call the 'fetchDriveDocument' tool if a file ID is available.
2. If the event source is "Trello", call the 'fetchTrelloCard' tool if a card ID is available.
3. Analyze the content:
   - If the content refers to updating the restaurant's menu, food items, or website content, execute the 'updateAstroWebsiteDB' tool.
   - If the content refers to marketing announcements, social posts, or special promotional events, execute the 'publishGoogleBusinessPost' tool.
4. Return a clear administrative decision output based on the tool invocation result.`, input.Source, input.Event, input.Payload)

			resp, err := genkit.Generate(ctx, g,
				ai.WithModelName("googleai/gemini-flash-latest"),
				ai.WithConfig(&genai.GenerateContentConfig{
					ThinkingConfig: &genai.ThinkingConfig{
						ThinkingLevel: genai.ThinkingLevelMinimal,
					},
				}),
				ai.WithTools(
					fetchDriveDocumentTool,
					fetchTrelloCardTool,
					updateAstroWebsiteDBTool,
					publishGoogleBusinessPostTool,
				),
				ai.WithPrompt(prompt),
			)
			if err != nil {
				return nil, fmt.Errorf("failed to generate administrative decision: %w", err)
			}

			// Parse response summary
			summaryText := resp.Text()
			if summaryText == "" {
				summaryText = "Administrative action completed successfully."
			}

			return &AdminDecisionResult{
				ActionTaken: "AutomatedZeroUIAction",
				Target:      "RestaurantEcosystem",
				Summary:     summaryText,
				Success:     true,
			}, nil
		},
	)
}
