import { redirect } from "next/navigation";

/** Legacy route — canonical path is /technology */
export default function TechnologiesRedirect() {
  redirect("/technology");
}
