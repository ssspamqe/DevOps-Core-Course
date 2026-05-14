interface AppEnv {
	APP_NAME: string;
	COURSE_NAME: string;
	DEPLOYMENT_ENV: string;
	WORKER_VERSION: string;
	DEPLOYED_AT: string;
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	SETTINGS: KVNamespace;
}

const json = (data: unknown, init?: ResponseInit) => Response.json(data, init);

const maskEmail = (value: string) => {
	const [localPart = "", domain = "unknown"] = value.split("@");
	return `${localPart.slice(0, 2) || "**"}***@${domain}`;
};

const getSecretState = (env: AppEnv) => ({
	apiTokenConfigured: Boolean(env.API_TOKEN),
	adminContact: env.ADMIN_EMAIL ? maskEmail(env.ADMIN_EMAIL) : "not-configured-locally",
});

const getDeploymentMetadata = (env: AppEnv) => ({
	app: env.APP_NAME,
	course: env.COURSE_NAME,
	environment: env.DEPLOYMENT_ENV,
	version: env.WORKER_VERSION,
	deployedAt: env.DEPLOYED_AT,
	runtime: "cloudflare-workers",
	secretChecks: getSecretState(env),
});

export default {
	async fetch(request: Request, env: AppEnv): Promise<Response> {
		const url = new URL(request.url);
		console.log("request", {
			path: url.pathname,
			colo: request.cf?.colo,
			country: request.cf?.country,
		});

		if (url.pathname === "/") {
			return json({
				...getDeploymentMetadata(env),
				message: "Hello from Cloudflare Workers",
				routes: ["/", "/health", "/deployment", "/edge", "/counter"],
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/health") {
			return json({
				status: "ok",
				service: env.APP_NAME,
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/deployment") {
			return json({
				...getDeploymentMetadata(env),
				requestId: crypto.randomUUID(),
			});
		}

		if (url.pathname === "/edge") {
			return json({
				...getDeploymentMetadata(env),
				edge: {
					colo: request.cf?.colo ?? null,
					country: request.cf?.country ?? null,
					city: request.cf?.city ?? null,
					asn: request.cf?.asn ?? null,
					httpProtocol: request.cf?.httpProtocol ?? null,
					tlsVersion: request.cf?.tlsVersion ?? null,
				},
				url: request.url,
			});
		}

		if (url.pathname === "/counter") {
			const rawVisits = await env.SETTINGS.get("visits");
			const visits = Number(rawVisits ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));

			return json({
				visits,
				persisted: true,
				storage: "workers-kv",
			});
		}

		return json(
			{
				error: "Not Found",
				path: url.pathname,
			},
			{ status: 404 },
		);
	},
} satisfies ExportedHandler<AppEnv>;
