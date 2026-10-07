FROM eclipse-temurin:21-jre-jammy AS jre

FROM node:22-slim

COPY --from=jre /opt/java/openjdk /opt/java/openjdk
ENV PATH="/opt/java/openjdk/bin:${PATH}"

RUN npm install -g firebase-tools

WORKDIR /app
COPY firebase.json .firebaserc ./

EXPOSE 4000 8081 9099
# Exports to a subdirectory, not /data itself: firebase replaces the export dir
# with rmdir+mkdir, which fails with EBUSY if that path is the volume mount point.
CMD ["firebase", "emulators:start", "--only", "firestore,auth", "--import=/data/export", "--export-on-exit=/data/export"]
