# syntax=docker/dockerfile:1
# Keycloak for Azure: an optimized PostgreSQL build with the realm baked in. Local development
# uses the stock image instead (compose.yaml). Settings come from Terraform (infra/terraform/auth.tf).

FROM quay.io/keycloak/keycloak:26.8.1 AS build
ENV KC_DB=postgres KC_HEALTH_ENABLED=true
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.8.1 AS prod
COPY --from=build /opt/keycloak/ /opt/keycloak/
COPY realm-app.json /opt/keycloak/data/import/realm-app.json
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--optimized", "--import-realm"]
