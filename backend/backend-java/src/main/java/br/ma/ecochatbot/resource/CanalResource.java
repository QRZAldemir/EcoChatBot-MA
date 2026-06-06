/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 *
 * Backend: DESENVOLVE APIs REST consumidas pelo frontend e por integrações
 * externas (WhatsApp Business / Evolution API · DeepSeek AI).
 */
package br.ma.ecochatbot.resource;

import br.ma.ecochatbot.dto.CanalDTO;
import br.ma.ecochatbot.entity.Canal;
import br.ma.ecochatbot.service.CanalService;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;

/**
 * API REST de Canais de Atendimento.
 *
 * Canais são configurados pelo gestor via frontend Angular e definem
 * os fluxos conversacionais do WhatsApp (Ambulatório, Exames, Ouvidoria, etc.).
 *
 * Endpoints expostos:
 *   GET    /api/canais        → lista todos os canais
 *   GET    /api/canais/{id}   → busca canal por ID (404 se não existe)
 *   POST   /api/canais        → cria novo canal (201 Created)
 *   PUT    /api/canais/{id}   → atualiza canal existente
 *   DELETE /api/canais/{id}   → remove canal (204 No Content)
 */
@Path("/api/canais")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class CanalResource {

    @Inject
    CanalService service;

    @GET
    public List<Canal> listar() {
        return service.listar();
    }

    @GET
    @Path("/{id}")
    public Response buscarPorId(@PathParam("id") Long id) {
        return service.buscarPorId(id)
            .map(c -> Response.ok(c).build())
            .orElse(Response.status(Response.Status.NOT_FOUND)
                .entity("Canal não encontrado: " + id).build());
    }

    @POST
    public Response criar(CanalDTO dto) {
        Canal criado = service.criar(dto);
        // 201 Created com o recurso criado no corpo — padrão REST
        return Response.status(Response.Status.CREATED).entity(criado).build();
    }

    @PUT
    @Path("/{id}")
    public Response atualizar(@PathParam("id") Long id, CanalDTO dto) {
        return service.atualizar(id, dto)
            .map(c -> Response.ok(c).build())
            .orElse(Response.status(Response.Status.NOT_FOUND)
                .entity("Canal não encontrado: " + id).build());
    }

    @DELETE
    @Path("/{id}")
    public Response deletar(@PathParam("id") Long id) {
        boolean removido = service.deletar(id);
        if (removido) {
            // 204 No Content — DELETE bem-sucedido sem corpo de resposta
            return Response.noContent().build();
        }
        return Response.status(Response.Status.NOT_FOUND)
            .entity("Canal não encontrado: " + id).build();
    }
}
