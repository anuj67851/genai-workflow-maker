### Objective of the Workflow

When a user submits a query, this workflow will:
1.  **Triage** the issue into one of three categories: `Hardware`, `Software`, or `Access`.
2.  **For Hardware issues:** It will check the device warranty and then ask the user for specific details about the physical problem.
3.  **For Software issues:** It will skip the warranty check and directly ask the user to describe the software problem.
4.  **For Access issues:** It will also skip the warranty check and ask for details about the access problem.
5.  **Finally:** After gathering the necessary details from the user (regardless of the path taken), it will create a single, detailed support ticket and inform the user of the ticket number.

---

### Step-by-Step Build Guide

First, go to the **Builder** view and ensure you have a blank canvas (refresh the page if needed).

#### Step 1: Name the Workflow
In the **Sidebar** on the left:
- **Workflow Name:** `Comprehensive IT Support Agent`
- **Workflow Description:** `Diagnoses Hardware, Software, and Access issues, asks for details, and creates a support ticket.`

#### Step 2: The Initial Triage (Tool Node)
- **Drag & Connect:** Drag a **"Tool / Agent"** node to the canvas and connect it to the **`START`** node.
- **Configure:** Select the node and configure it in the Inspector Panel:
    - **Description:** `Triage the user's IT problem.`
    - **Prompt / Instruction:** `Triage this IT issue based on the user's initial request: {query}`
- **Rename ID (Optional but recommended):** Double-click the node's title on the canvas and rename it to `triage-issue`.

#### Step 3: First Decision - Is it Hardware? (Condition Node)
- **Drag & Connect:** Drag a **"Condition"** node and connect the output of `triage-issue` to its input.
- **Configure:**
    - **Description:** `Check if the category is 'Hardware'.`
    - **Prompt / Instruction:** `Based on the history, did the 'triage-issue' step return a category of 'Hardware'? Respond with only TRUE or FALSE.`
- **Rename ID:** `check-if-hardware`

#### Step 4: Second Decision - Is it Software? (Condition Node)
This is where we create the three-way split. This node will only be reached if the first condition was **False**.
- **Drag & Connect:** Drag another **"Condition"** node to the canvas. Connect the **FALSE (red)** handle of `check-if-hardware` to this new node's input.
- **Configure:**
    - **Description:** `Check if the category is 'Software'.`
    - **Prompt / Instruction:** `Based on the history, did the 'triage-issue' step return a category of 'Software'? Respond with only TRUE or FALSE.`
- **Rename ID:** `check-if-software`

#### Step 5: The Hardware Branch
- **Drag & Connect:** Drag a **"Tool / Agent"** node. Connect the **TRUE (green)** handle of `check-if-hardware` to its input.
- **Configure:**
    - **Description:** `Check device warranty for the user.`
    - **Prompt / Instruction:** `Check the device warranty for user: {context.username}`
- **Rename ID:** `check-warranty`

#### Step 6: The "Ask for Details" Nodes (Human Input)
We need three separate "ask" nodes, one for each branch, to provide a tailored question to the user.
**This is the key:** They will all save their output to the **same variable name**, `issue_details`.

1.  **Ask about Hardware:**
    - **Drag & Connect:** Drag a **"Human Input"** node. Connect the output of `check-warranty` to its input.
    - **Configure:**
        - **Description:** `Ask user for hardware problem details.`
        - **Prompt / Instruction:** `I see this is a hardware issue. To help the technician, could you please describe the physical damage or problem in detail?`
        - **Output Variable Name:** `issue_details`
    - **Rename ID:** `ask-hardware-details`

2.  **Ask about Software:**
    - **Drag & Connect:** Drag a **"Human Input"** node. Connect the **TRUE (green)** handle of `check-if-software` to its input.
    - **Configure:**
        - **Description:** `Ask user for software problem details.`
        - **Prompt / Instruction:** `I understand you're having a software problem. Can you please describe what you are seeing? Include any error messages.`
        - **Output Variable Name:** `issue_details`
    - **Rename ID:** `ask-software-details`

3.  **Ask about Access (The "Default" Path):**
    - **Drag & Connect:** Drag a **"Human Input"** node. Connect the **FALSE (red)** handle of `check-if-software` to its input. (If it's not Hardware and not Software, it must be Access).
    - **Configure:**
        - **Description:** `Ask user for access problem details.`
        - **Prompt / Instruction:** `It looks like you're having an access issue. Can you please tell me exactly what you are trying to log into or access?`
        - **Output Variable Name:** `issue_details`
    - **Rename ID:** `ask-access-details`

#### Step 7: The Merge Point - Create the Ticket (Tool Node)
All three branches will now converge on this single node.
- **Drag & Connect:** Drag a **"Tool / Agent"** node onto the canvas.
- **Connect All Three Paths:**
    1.  Connect the output of `ask-hardware-details` to this node's input.
    2.  Connect the output of `ask-software-details` to this node's input.
    3.  Connect the output of `ask-access-details` to this node's input.
- **Configure:**
    - **Description:** `Create a detailed support ticket.`
    - **Prompt / Instruction:** `Create a support ticket for user '{context.username}'. The detailed problem description provided by the user is: {input.issue_details}`
- **Rename ID:** `create-final-ticket`

#### Step 8: Final Confirmation (LLM Response)
- **Drag & Connect:** Drag an **"LLM Response"** node. Connect the output of `create-final-ticket` to its input.
- **Configure:**
    - **Description:** `Inform the user the ticket was created.`
    - **Prompt / Instruction:** `Politely inform the user that their support ticket has been successfully created using the details they provided. Look at the history for the output of the 'create-final-ticket' step and provide them with their new ticket ID.`
- **Rename ID:** `inform-user`

#### Step 9: End the Workflow
- Connect the output of the `inform-user` node to the input of the **`END`** node.

#### Step 10: Save and Test
- Click **"Save Workflow"** in the sidebar.
- Navigate to the **"Run Workflows"** tab and select your "Comprehensive IT Support Agent."

---

### How to Test Each Branch

-   **Test the Hardware Path:**
    1.  **You:** `My keyboard is broken.`
    2.  **Bot:** `I see this is a hardware issue. To help the technician, could you please describe the physical damage or problem in detail?`
    3.  **You:** `The 'S' key fell off and I can't reattach it.`
    4.  **Bot:** `Your support ticket has been successfully created... Your new ticket ID is IT-XXXX.`

-   **Test the Software Path:**
    1.  **You:** `The VPN client keeps crashing on my machine.`
    2.  **Bot:** `I understand you're having a software problem. Can you please describe what you are seeing? Include any error messages.`
    3.  **You:** `It just closes itself about 10 seconds after I connect. There is no error message.`
    4.  **Bot:** `Your support ticket has been successfully created... Your new ticket ID is IT-XXXX.`

-   **Test the Access Path:**
    1.  **You:** `I'm locked out.`
    2.  **Bot:** `It looks like you're having an access issue. Can you please tell me exactly what you are trying to log into or access?`
    3.  **You:** `I can't log into the main HR portal.`
    4.  **Bot:** `Your support ticket has been successfully created... Your new ticket ID is IT-XXXX.`