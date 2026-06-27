const BedtimeReminderPlugin = async (input, options) => {
  return {
    "experimental.chat.system.transform": async (input, output) => {
      const now = new Date();

      // Format current local date and time
      const dateString = now.toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric"
      });

      const timeString = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
      });

      const hours = now.getHours();
      let nudgeInstruction = "";

      // Nudge between 1:00 AM (inclusive) and 8:00 AM (exclusive)
      if (hours >= 1 && hours < 8) {
        nudgeInstruction = `\n- **CRITICAL REMINDER**: The current local time is past 1:00 AM (it is ${timeString}). You MUST nudge the user to stop working and go to bed. Remind them to save their work (e.g., using the \`/goodnight\` command) and log off. Keep your tone helpful, firm, and focused on wrapping up the current session.`;
      }

      // Construct environment state block
      const envBlock = `
[Persistent Environment State]
- Current Date: ${dateString}
- Current Time: ${timeString}
${nudgeInstruction}
`.trim();

      // Append environment block to system instructions
      output.system.push(envBlock);
    }
  };
};

export default BedtimeReminderPlugin;
export const server = BedtimeReminderPlugin;
